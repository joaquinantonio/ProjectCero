from uuid import uuid4

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models

from apps.core.models import TimeStampedModel


class Order(TimeStampedModel):
    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        PENDING_PAYMENT = "pending_payment", "Pending Payment"
        PAID = "paid", "Paid"
        CANCELLED = "cancelled", "Cancelled"
        EXPIRED = "expired", "Expired"
        REFUNDED = "refunded", "Refunded"
        PARTIALLY_REFUNDED = "partially_refunded", "Partially Refunded"

    reference_code = models.CharField(max_length=32, unique=True, blank=True)

    customer_name = models.CharField(max_length=150)
    customer_email = models.EmailField()
    customer_phone = models.CharField(max_length=50, blank=True)

    status = models.CharField(
        max_length=30,
        choices=Status.choices,
        default=Status.DRAFT,
    )

    currency = models.CharField(max_length=3, default="MYR")
    subtotal_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0)],
    )
    discount_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0)],
    )
    tax_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0)],
    )
    total_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0)],
    )

    admin_notes = models.TextField(blank=True)

    inventory_committed_at = models.DateTimeField(
        blank=True,
        null=True,
        editable=False,
        help_text="Set when stock/ticket inventory has been committed for this order.",
    )
    inventory_released_at = models.DateTimeField(
        blank=True,
        null=True,
        editable=False,
        help_text="Set when previously committed inventory has been released.",
    )

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["status", "created_at"]),
            models.Index(fields=["reference_code"]),
            models.Index(fields=["customer_email"]),
            models.Index(fields=["currency", "total_amount"]),
            models.Index(fields=["status", "inventory_committed_at"]),
        ]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(subtotal_amount__gte=0),
                name="order_subtotal_amount_non_negative",
            ),
            models.CheckConstraint(
                condition=models.Q(discount_amount__gte=0),
                name="order_discount_amount_non_negative",
            ),
            models.CheckConstraint(
                condition=models.Q(tax_amount__gte=0),
                name="order_tax_amount_non_negative",
            ),
            models.CheckConstraint(
                condition=models.Q(total_amount__gte=0),
                name="order_total_amount_non_negative",
            ),
        ]

    def generate_reference_code(self):
        while True:
            reference_code = f"ORD-{uuid4().hex[:8].upper()}"

            exists = Order.objects.filter(
                reference_code=reference_code
            ).exclude(pk=self.pk).exists()

            if not exists:
                return reference_code

    def recalculate_totals(self, save=True):
        subtotal = sum(item.total_amount for item in self.items.all())
        total = subtotal - self.discount_amount + self.tax_amount

        self.subtotal_amount = subtotal
        self.total_amount = max(total, 0)

        if save:
            self.save(update_fields=["subtotal_amount", "total_amount", "updated_at"])

    def save(self, *args, **kwargs):
        if not self.reference_code:
            self.reference_code = self.generate_reference_code()

            update_fields = kwargs.get("update_fields")
            if update_fields is not None:
                kwargs["update_fields"] = set(update_fields) | {"reference_code"}

        super().save(*args, **kwargs)

    @property
    def is_inventory_committed(self):
        return self.inventory_committed_at is not None

    @property
    def can_commit_inventory(self):
        return self.status == self.Status.PAID and not self.is_inventory_committed

    @property
    def can_release_inventory(self):
        releasable_statuses = {
            self.Status.CANCELLED,
            self.Status.EXPIRED,
            self.Status.REFUNDED,
        }
        return self.status in releasable_statuses and self.is_inventory_committed

    def __str__(self):
        return self.reference_code or f"Order for {self.customer_email}"


class OrderItem(TimeStampedModel):
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name="items",
    )

    merch_item = models.ForeignKey(
        "merch.MerchItem",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="order_items",
    )

    ticket_type = models.ForeignKey(
        "events.TicketType",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="order_items",
    )

    description = models.CharField(max_length=255)
    quantity = models.PositiveIntegerField(
        default=1,
        validators=[MinValueValidator(1)],
    )

    unit_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)],
    )
    total_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)],
    )

    class Meta:
        ordering = ["id"]
        indexes = [
            models.Index(fields=["order"]),
            models.Index(fields=["merch_item"]),
            models.Index(fields=["ticket_type"]),
        ]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(quantity__gte=1),
                name="order_item_quantity_positive",
            ),
            models.CheckConstraint(
                condition=models.Q(unit_amount__gte=0),
                name="order_item_unit_amount_non_negative",
            ),
            models.CheckConstraint(
                condition=models.Q(total_amount__gte=0),
                name="order_item_total_amount_non_negative",
            ),
            models.CheckConstraint(
                condition=(
                    (
                        models.Q(merch_item__isnull=False)
                        & models.Q(ticket_type__isnull=True)
                    )
                    | (
                        models.Q(merch_item__isnull=True)
                        & models.Q(ticket_type__isnull=False)
                    )
                ),
                name="order_item_exactly_one_sellable_item",
            ),
        ]

    def clean(self):
        super().clean()

        if self.merch_item_id and self.ticket_type_id:
            raise ValidationError(
                "Order item cannot link to both a merch item and a ticket type."
            )

        if not self.merch_item_id and not self.ticket_type_id:
            raise ValidationError(
                "Order item must link to either a merch item or a ticket type."
            )

    def save(self, *args, **kwargs):
        self.total_amount = self.quantity * self.unit_amount
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.description} x {self.quantity}"


class OrderHistory(TimeStampedModel):
    class EventType(models.TextChoices):
        CREATED = "created", "Created"
        STATUS_CHANGED = "status_changed", "Status Changed"
        INVENTORY_COMMITTED = "inventory_committed", "Inventory Committed"
        INVENTORY_RELEASED = "inventory_released", "Inventory Released"
        EMAIL_SENT = "email_sent", "Email Sent"
        EMAIL_SKIPPED = "email_skipped", "Email Skipped"
        NOTE = "note", "Note"
        ERROR = "error", "Error"

    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name="history_entries",
    )

    event_type = models.CharField(
        max_length=40,
        choices=EventType.choices,
    )

    from_status = models.CharField(
        max_length=30,
        choices=Order.Status.choices,
        blank=True,
    )
    to_status = models.CharField(
        max_length=30,
        choices=Order.Status.choices,
        blank=True,
    )

    message = models.TextField(blank=True)

    metadata = models.JSONField(
        default=dict,
        blank=True,
        help_text="Structured audit metadata for future payment/webhook events.",
    )

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="order_history_entries",
    )

    class Meta:
        ordering = ["-created_at", "-id"]
        verbose_name = "Order history"
        verbose_name_plural = "Order history"
        indexes = [
            models.Index(fields=["order", "created_at"]),
            models.Index(fields=["event_type", "created_at"]),
            models.Index(fields=["from_status", "to_status"]),
        ]

    def __str__(self):
        return f"{self.order.reference_code} - {self.get_event_type_display()}"