from datetime import timedelta
from decimal import Decimal

from django.core import mail
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from apps.events.models import Event, EventCategory, TicketType
from apps.merch.models import MerchItem

from .audit import record_order_created
from .models import Order, OrderHistory, OrderItem, PaymentProof
from .workflow import change_order_status


@override_settings(
    EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
    ORDER_NOTIFICATION_EMAIL="orders@example.com",
    DEFAULT_FROM_EMAIL="CeroPJ <no-reply@example.com>",
)
class OrderWorkflowTests(TestCase):
    def create_merch_item(
        self,
        name="Cero Tee",
        price_amount=Decimal("50.00"),
        stock_quantity=5,
        track_stock=True,
    ):
        return MerchItem.objects.create(
            name=name,
            price_amount=price_amount,
            currency="MYR",
            track_stock=track_stock,
            stock_quantity=stock_quantity,
            is_active=True,
        )

    def create_merch_order(self, merch_item, quantity=2):
        order = Order.objects.create(
            customer_name="Test Customer",
            customer_email="customer@example.com",
            customer_phone="0123456789",
            status=Order.Status.PENDING_PAYMENT,
            currency=merch_item.currency,
        )

        OrderItem.objects.create(
            order=order,
            merch_item=merch_item,
            description=merch_item.name,
            quantity=quantity,
            unit_amount=merch_item.price_amount,
            total_amount=Decimal("0.00"),
        )

        order.recalculate_totals(save=True)
        return order

    def create_ticket_type(
        self,
        quantity_total=10,
        quantity_sold=0,
        price_amount=Decimal("30.00"),
    ):
        category = EventCategory.objects.create(
            name="Music",
            is_active=True,
        )

        event = Event.objects.create(
            category=category,
            title="Live Night",
            start_at=timezone.now() + timedelta(days=7),
            status=Event.Status.PUBLISHED,
        )

        return TicketType.objects.create(
            event=event,
            name="General Admission",
            price_amount=price_amount,
            currency="MYR",
            quantity_total=quantity_total,
            quantity_sold=quantity_sold,
            is_active=True,
        )

    def create_ticket_order(self, ticket_type, quantity=3):
        order = Order.objects.create(
            customer_name="Ticket Customer",
            customer_email="ticket@example.com",
            customer_phone="0123456789",
            status=Order.Status.PENDING_PAYMENT,
            currency=ticket_type.currency,
        )

        OrderItem.objects.create(
            order=order,
            ticket_type=ticket_type,
            description=f"{ticket_type.event.title} - {ticket_type.name}",
            quantity=quantity,
            unit_amount=ticket_type.price_amount,
            total_amount=Decimal("0.00"),
        )

        order.recalculate_totals(save=True)
        return order

    def test_order_total_and_created_history_can_be_recorded(self):
        merch_item = self.create_merch_item(price_amount=Decimal("50.00"))
        order = self.create_merch_order(merch_item, quantity=2)

        record_order_created(order, source="test")

        order.refresh_from_db()

        self.assertEqual(order.total_amount, Decimal("100.00"))
        self.assertEqual(order.subtotal_amount, Decimal("100.00"))

        history = OrderHistory.objects.get(
            order=order,
            event_type=OrderHistory.EventType.CREATED,
        )
        self.assertEqual(history.to_status, Order.Status.PENDING_PAYMENT)
        self.assertEqual(history.metadata["source"], "test")

    def test_public_merch_order_creates_order_history_and_emails(self):
        merch_item = self.create_merch_item(price_amount=Decimal("50.00"))

        response = self.client.post(
            reverse("orders:create_merch_order", args=[merch_item.slug]),
            {
                "customer_name": "Public Buyer",
                "customer_email": "buyer@example.com",
                "customer_phone": "0123456789",
                "quantity": 2,
            },
        )

        order = Order.objects.get()

        self.assertRedirects(
            response,
            reverse("orders:order_success", args=[order.reference_code]),
        )

        self.assertEqual(order.status, Order.Status.PENDING_PAYMENT)
        self.assertEqual(order.total_amount, Decimal("100.00"))
        self.assertEqual(order.items.count(), 1)

        self.assertEqual(len(mail.outbox), 2)

        self.assertEqual(
            order.history_entries.filter(
                event_type=OrderHistory.EventType.CREATED,
            ).count(),
            1,
        )
        self.assertEqual(
            order.history_entries.filter(
                event_type=OrderHistory.EventType.EMAIL_SENT,
            ).count(),
            2,
        )

        merch_item.refresh_from_db()
        self.assertEqual(merch_item.stock_quantity, 5)

    def test_public_ticket_order_creates_order_history_and_emails(self):
        ticket_type = self.create_ticket_type(
            quantity_total=10,
            quantity_sold=0,
            price_amount=Decimal("30.00"),
        )

        response = self.client.post(
            reverse("orders:create_ticket_order", args=[ticket_type.pk]),
            {
                "customer_name": "Ticket Buyer",
                "customer_email": "ticketbuyer@example.com",
                "customer_phone": "0123456789",
                "quantity": 3,
            },
        )

        order = Order.objects.get()

        self.assertRedirects(
            response,
            reverse("orders:order_success", args=[order.reference_code]),
        )

        self.assertEqual(order.status, Order.Status.PENDING_PAYMENT)
        self.assertEqual(order.total_amount, Decimal("90.00"))
        self.assertEqual(order.items.count(), 1)

        self.assertEqual(len(mail.outbox), 2)

        self.assertEqual(
            order.history_entries.filter(
                event_type=OrderHistory.EventType.CREATED,
            ).count(),
            1,
        )
        self.assertEqual(
            order.history_entries.filter(
                event_type=OrderHistory.EventType.EMAIL_SENT,
            ).count(),
            2,
        )

        ticket_type.refresh_from_db()
        self.assertEqual(ticket_type.quantity_sold, 0)

    def test_marking_merch_order_paid_commits_inventory_once(self):
        merch_item = self.create_merch_item(stock_quantity=5)
        order = self.create_merch_order(merch_item, quantity=2)

        order, status_changed, inventory_changed = change_order_status(
            order.pk,
            Order.Status.PAID,
            source="test",
        )

        self.assertTrue(status_changed)
        self.assertTrue(inventory_changed)

        order.refresh_from_db()
        merch_item.refresh_from_db()

        self.assertEqual(order.status, Order.Status.PAID)
        self.assertIsNotNone(order.inventory_committed_at)
        self.assertEqual(merch_item.stock_quantity, 3)

        self.assertEqual(
            order.history_entries.filter(
                event_type=OrderHistory.EventType.STATUS_CHANGED,
            ).count(),
            1,
        )
        self.assertEqual(
            order.history_entries.filter(
                event_type=OrderHistory.EventType.INVENTORY_COMMITTED,
            ).count(),
            1,
        )

        order, status_changed, inventory_changed = change_order_status(
            order.pk,
            Order.Status.PAID,
            source="test",
        )

        self.assertFalse(status_changed)
        self.assertFalse(inventory_changed)

        merch_item.refresh_from_db()
        self.assertEqual(merch_item.stock_quantity, 3)

        self.assertEqual(
            order.history_entries.filter(
                event_type=OrderHistory.EventType.INVENTORY_COMMITTED,
            ).count(),
            1,
        )

    def test_refunding_merch_order_releases_inventory_once(self):
        merch_item = self.create_merch_item(stock_quantity=5)
        order = self.create_merch_order(merch_item, quantity=2)

        change_order_status(order.pk, Order.Status.PAID, source="test")
        change_order_status(order.pk, Order.Status.REFUNDED, source="test")

        order.refresh_from_db()
        merch_item.refresh_from_db()

        self.assertEqual(order.status, Order.Status.REFUNDED)
        self.assertIsNone(order.inventory_committed_at)
        self.assertIsNotNone(order.inventory_released_at)
        self.assertEqual(merch_item.stock_quantity, 5)

        self.assertEqual(
            order.history_entries.filter(
                event_type=OrderHistory.EventType.INVENTORY_RELEASED,
            ).count(),
            1,
        )

        change_order_status(order.pk, Order.Status.REFUNDED, source="test")

        merch_item.refresh_from_db()
        self.assertEqual(merch_item.stock_quantity, 5)

        self.assertEqual(
            order.history_entries.filter(
                event_type=OrderHistory.EventType.INVENTORY_RELEASED,
            ).count(),
            1,
        )

    def test_marking_ticket_order_paid_and_refunded_updates_quantity_sold(self):
        ticket_type = self.create_ticket_type(quantity_total=10, quantity_sold=0)
        order = self.create_ticket_order(ticket_type, quantity=3)

        change_order_status(order.pk, Order.Status.PAID, source="test")

        order.refresh_from_db()
        ticket_type.refresh_from_db()

        self.assertEqual(order.status, Order.Status.PAID)
        self.assertEqual(ticket_type.quantity_sold, 3)

        self.assertEqual(
            order.history_entries.filter(
                event_type=OrderHistory.EventType.INVENTORY_COMMITTED,
            ).count(),
            1,
        )

        change_order_status(order.pk, Order.Status.REFUNDED, source="test")

        order.refresh_from_db()
        ticket_type.refresh_from_db()

        self.assertEqual(order.status, Order.Status.REFUNDED)
        self.assertEqual(ticket_type.quantity_sold, 0)

        self.assertEqual(
            order.history_entries.filter(
                event_type=OrderHistory.EventType.INVENTORY_RELEASED,
            ).count(),
            1,
        )

    def test_insufficient_merch_stock_does_not_mark_order_paid(self):
        merch_item = self.create_merch_item(stock_quantity=1)
        order = self.create_merch_order(merch_item, quantity=2)

        with self.assertRaises(ValidationError):
            change_order_status(
                order.pk,
                Order.Status.PAID,
                source="test",
            )

        order.refresh_from_db()
        merch_item.refresh_from_db()

        self.assertEqual(order.status, Order.Status.PENDING_PAYMENT)
        self.assertIsNone(order.inventory_committed_at)
        self.assertEqual(merch_item.stock_quantity, 1)

        self.assertFalse(
            order.history_entries.filter(
                event_type=OrderHistory.EventType.INVENTORY_COMMITTED,
            ).exists()
        )
        self.assertFalse(
            order.history_entries.filter(
                event_type=OrderHistory.EventType.STATUS_CHANGED,
            ).exists()
        )

    def test_insufficient_ticket_quantity_does_not_mark_order_paid(self):
        ticket_type = self.create_ticket_type(
            quantity_total=2,
            quantity_sold=0,
        )
        order = self.create_ticket_order(ticket_type, quantity=3)

        with self.assertRaises(ValidationError):
            change_order_status(
                order.pk,
                Order.Status.PAID,
                source="test",
            )

        order.refresh_from_db()
        ticket_type.refresh_from_db()

        self.assertEqual(order.status, Order.Status.PENDING_PAYMENT)
        self.assertIsNone(order.inventory_committed_at)
        self.assertEqual(ticket_type.quantity_sold, 0)

        self.assertFalse(
            order.history_entries.filter(
                event_type=OrderHistory.EventType.INVENTORY_COMMITTED,
            ).exists()
        )
        self.assertFalse(
            order.history_entries.filter(
                event_type=OrderHistory.EventType.STATUS_CHANGED,
            ).exists()
        )

    def test_order_success_uploads_and_updates_payment_proof_in_place(self):
        merch_item = self.create_merch_item(price_amount=Decimal("50.00"))
        order = self.create_merch_order(merch_item, quantity=1)

        url = reverse("orders:order_success", args=[order.reference_code])

        first_file = SimpleUploadedFile("proof-1.png", b"proof-one", content_type="image/png")
        response = self.client.post(
            url,
            {
                "file": first_file,
                "notes": "First upload",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(PaymentProof.objects.count(), 1)

        proof = PaymentProof.objects.get(order=order)
        first_pk = proof.pk
        self.assertEqual(proof.notes, "First upload")

        second_file = SimpleUploadedFile("proof-2.png", b"proof-two", content_type="image/png")
        response = self.client.post(
            url,
            {
                "file": second_file,
                "notes": "Updated upload",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(PaymentProof.objects.count(), 1)

        proof.refresh_from_db()
        self.assertEqual(proof.pk, first_pk)
        self.assertEqual(proof.notes, "Updated upload")
