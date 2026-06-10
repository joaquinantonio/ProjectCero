from decimal import Decimal

from django.contrib import admin
from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils.html import strip_tags

from apps.merch.models import MerchItem

from .admin import OrderAdmin, OrderHistoryAdmin
from .models import Order, OrderHistory, OrderItem
from .workflow import change_order_status


@override_settings(
    EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
    ORDER_NOTIFICATION_EMAIL="orders@example.com",
    DEFAULT_FROM_EMAIL="CeroPJ <no-reply@example.com>",
)
class OrderAdminUsabilityTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.superuser = User.objects.create_superuser(
            username="admin",
            email="admin@example.com",
            password="password123",
        )
        self.client.force_login(self.superuser)
        self.order_admin = OrderAdmin(Order, admin.site)
        self.history_admin = OrderHistoryAdmin(OrderHistory, admin.site)

    def create_merch_item(self, name="Cero Tee", stock_quantity=5):
        return MerchItem.objects.create(
            name=name,
            price_amount=Decimal("50.00"),
            currency="MYR",
            track_stock=True,
            stock_quantity=stock_quantity,
            is_active=True,
        )

    def create_merch_order(self, merch_item, quantity=2, status=Order.Status.PENDING_PAYMENT):
        order = Order.objects.create(
            customer_name="Test Customer",
            customer_email="customer@example.com",
            customer_phone="0123456789",
            status=status,
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

    def test_order_change_page_loads_without_crashing(self):
        merch_item = self.create_merch_item()
        order = self.create_merch_order(merch_item)

        response = self.client.get(
            reverse("admin:orders_order_change", args=[order.pk])
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Order Summary")
        self.assertContains(response, order.reference_code)
        self.assertContains(response, merch_item.name)

    def test_order_summary_renders_item_and_human_status(self):
        merch_item = self.create_merch_item()
        order = self.create_merch_order(merch_item)

        html = self.order_admin.order_summary(order)
        text = strip_tags(str(html))

        self.assertIn(order.reference_code, text)
        self.assertIn("Pending Payment", text)
        self.assertIn("Not committed", text)
        self.assertIn("Cero Tee", text)
        self.assertIn("MYR 100.00", text)

    def test_history_status_transition_uses_human_labels(self):
        merch_item = self.create_merch_item()
        order = self.create_merch_order(merch_item)

        history = OrderHistory.objects.create(
            order=order,
            event_type=OrderHistory.EventType.STATUS_CHANGED,
            from_status=Order.Status.PENDING_PAYMENT,
            to_status=Order.Status.PAID,
            message="Status changed.",
        )

        self.assertEqual(
            self.history_admin.status_transition(history),
            "Pending Payment → Paid",
        )

    def test_admin_changelist_loads(self):
        merch_item = self.create_merch_item()
        order = self.create_merch_order(merch_item)

        response = self.client.get(reverse("admin:orders_order_changelist"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, order.reference_code)
        self.assertContains(response, "Not committed")

    def test_inventory_filter_committed(self):
        pending_item = self.create_merch_item(name="Pending Tee", stock_quantity=5)
        committed_item = self.create_merch_item(name="Committed Tee", stock_quantity=5)

        pending_order = self.create_merch_order(pending_item)
        committed_order = self.create_merch_order(committed_item)

        change_order_status(
            committed_order.pk,
            Order.Status.PAID,
            created_by=self.superuser,
            source="test",
        )

        response = self.client.get(
            reverse("admin:orders_order_changelist") + "?inventory=committed"
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, committed_order.reference_code)
        self.assertNotContains(response, pending_order.reference_code)

    def test_inventory_filter_released(self):
        active_item = self.create_merch_item(name="Active Tee", stock_quantity=5)
        released_item = self.create_merch_item(name="Released Tee", stock_quantity=5)

        active_order = self.create_merch_order(active_item)
        released_order = self.create_merch_order(released_item)

        change_order_status(
            released_order.pk,
            Order.Status.PAID,
            created_by=self.superuser,
            source="test",
        )
        change_order_status(
            released_order.pk,
            Order.Status.REFUNDED,
            created_by=self.superuser,
            source="test",
        )

        response = self.client.get(
            reverse("admin:orders_order_changelist") + "?inventory=released"
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, released_order.reference_code)
        self.assertNotContains(response, active_order.reference_code)

    def test_inventory_filter_needs_attention(self):
        merch_item = self.create_merch_item(name="Attention Tee", stock_quantity=5)

        needs_attention_order = self.create_merch_order(
            merch_item,
            status=Order.Status.PAID,
        )

        response = self.client.get(
            reverse("admin:orders_order_changelist") + "?inventory=needs_attention"
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, needs_attention_order.reference_code)
        self.assertContains(response, "Needs attention")