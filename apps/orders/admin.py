from django.contrib import admin
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.db.models import Q
from django.utils.html import format_html, format_html_join

from apps.core.admin import (
    SuperuserDeleteOnlyAdminMixin,
    TimestampedAdmin,
    render_admin_badge,
)

from .models import Order, OrderHistory, OrderItem
from .services import send_order_status_update
from .workflow import change_order_status


class InventoryStatusFilter(admin.SimpleListFilter):
    title = "inventory"
    parameter_name = "inventory"

    def lookups(self, request, model_admin):
        return (
            ("committed", "Committed"),
            ("not_committed", "Not committed"),
            ("released", "Released"),
            ("needs_attention", "Needs attention"),
        )

    def queryset(self, request, queryset):
        value = self.value()

        if value == "committed":
            return queryset.filter(inventory_committed_at__isnull=False)

        if value == "released":
            return queryset.filter(
                inventory_committed_at__isnull=True,
                inventory_released_at__isnull=False,
            )

        if value == "not_committed":
            return queryset.filter(
                inventory_committed_at__isnull=True,
                inventory_released_at__isnull=True,
            )

        if value == "needs_attention":
            return queryset.filter(
                Q(status=Order.Status.PAID, inventory_committed_at__isnull=True)
                | Q(
                    status__in=[
                        Order.Status.CANCELLED,
                        Order.Status.EXPIRED,
                        Order.Status.REFUNDED,
                    ],
                    inventory_committed_at__isnull=False,
                )
            )

        return queryset


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    autocomplete_fields = ("merch_item", "ticket_type")
    fields = (
        "description",
        "merch_item",
        "ticket_type",
        "quantity",
        "unit_amount",
        "total_amount",
    )
    readonly_fields = ("total_amount",)


class OrderHistoryInline(admin.TabularInline):
    model = OrderHistory
    extra = 0
    can_delete = False
    classes = ("collapse",)
    fields = (
        "created_at",
        "event_badge",
        "status_transition",
        "message",
        "created_by",
    )
    readonly_fields = fields
    ordering = ("-created_at", "-id")
    max_num = 0

    @admin.display(description="Event")
    def event_badge(self, obj):
        tone_map = {
            OrderHistory.EventType.CREATED: "success",
            OrderHistory.EventType.STATUS_CHANGED: "info",
            OrderHistory.EventType.INVENTORY_COMMITTED: "success",
            OrderHistory.EventType.INVENTORY_RELEASED: "warning",
            OrderHistory.EventType.EMAIL_SENT: "info",
            OrderHistory.EventType.EMAIL_SKIPPED: "neutral",
            OrderHistory.EventType.NOTE: "neutral",
            OrderHistory.EventType.ERROR: "danger",
        }
        return render_admin_badge(
            obj.get_event_type_display(),
            tone_map.get(obj.event_type, "neutral"),
        )

    @admin.display(description="Status")
    def status_transition(self, obj):
        if obj.from_status and obj.to_status:
            return f"{obj.get_from_status_display()} → {obj.get_to_status_display()}"

        if obj.to_status:
            return obj.get_to_status_display()

        return "-"

    def has_add_permission(self, request, obj=None):
        return False


def update_orders_status(modeladmin, request, queryset, status_value, label):
    updated = 0
    emailed = 0
    inventory_updated = 0
    failed = 0

    for selected_order in queryset:
        try:
            order, status_changed, inventory_changed = change_order_status(
                selected_order.pk,
                status_value,
                created_by=request.user,
                source="admin_bulk_action",
            )

            if not status_changed:
                continue

            updated += 1

            if inventory_changed:
                inventory_updated += 1

            if send_order_status_update(order):
                emailed += 1

        except ValidationError as exc:
            failed += 1
            modeladmin.message_user(
                request,
                f"{selected_order.reference_code}: {exc}",
                level=messages.ERROR,
            )

    modeladmin.message_user(
        request,
        (
            f"{updated} order(s) marked as {label}. "
            f"{inventory_updated} inventory update(s). "
            f"{emailed} customer email(s) sent. "
            f"{failed} failed."
        ),
        level=messages.SUCCESS if failed == 0 else messages.WARNING,
    )


@admin.action(description="Mark selected orders as Pending Payment")
def mark_pending_payment(modeladmin, request, queryset):
    update_orders_status(
        modeladmin,
        request,
        queryset,
        Order.Status.PENDING_PAYMENT,
        "Pending Payment",
    )


@admin.action(description="Mark selected orders as Paid")
def mark_paid(modeladmin, request, queryset):
    update_orders_status(
        modeladmin,
        request,
        queryset,
        Order.Status.PAID,
        "Paid",
    )


@admin.action(description="Mark selected orders as Cancelled")
def mark_cancelled(modeladmin, request, queryset):
    update_orders_status(
        modeladmin,
        request,
        queryset,
        Order.Status.CANCELLED,
        "Cancelled",
    )


@admin.action(description="Mark selected orders as Expired")
def mark_expired(modeladmin, request, queryset):
    update_orders_status(
        modeladmin,
        request,
        queryset,
        Order.Status.EXPIRED,
        "Expired",
    )


@admin.action(description="Mark selected orders as Refunded")
def mark_refunded(modeladmin, request, queryset):
    update_orders_status(
        modeladmin,
        request,
        queryset,
        Order.Status.REFUNDED,
        "Refunded",
    )


@admin.register(Order)
class OrderAdmin(SuperuserDeleteOnlyAdminMixin, TimestampedAdmin):
    list_display = (
        "reference_code",
        "customer_summary",
        "status_badge",
        "inventory_badge",
        "item_summary",
        "total_display",
        "created_at",
    )
    list_filter = (
        "status",
        InventoryStatusFilter,
        "currency",
        "created_at",
    )
    search_fields = (
        "reference_code",
        "customer_name",
        "customer_email",
        "customer_phone",
        "admin_notes",
        "items__description",
        "items__merch_item__name",
        "items__ticket_type__name",
        "items__ticket_type__event__title",
    )
    ordering = ("-created_at",)
    date_hierarchy = "created_at"
    list_select_related = ()
    inlines = [OrderItemInline, OrderHistoryInline]
    actions = [
        mark_pending_payment,
        mark_paid,
        mark_cancelled,
        mark_expired,
        mark_refunded,
    ]

    readonly_fields = (
        "reference_code",
        "order_summary",
        "subtotal_amount",
        "total_amount",
        "inventory_committed_at",
        "inventory_released_at",
        "created_at",
        "updated_at",
    )

    fieldsets = (
        (
            "Order Summary",
            {
                "fields": (
                    "order_summary",
                    "reference_code",
                ),
                "description": (
                    "Use this section to quickly understand the order before changing status."
                ),
            },
        ),
        (
            "Customer",
            {
                "fields": (
                    "customer_name",
                    "customer_email",
                    "customer_phone",
                ),
            },
        ),
        (
            "Order Status",
            {
                "fields": (
                    "status",
                    "currency",
                    "inventory_committed_at",
                    "inventory_released_at",
                ),
                "description": (
                    "Pending Payment = waiting for manual payment/admin confirmation. "
                    "Paid = payment confirmed and inventory committed. "
                    "Cancelled, Expired, or Refunded = inventory released if it was previously committed."
                ),
            },
        ),
        (
            "Totals",
            {
                "fields": (
                    "subtotal_amount",
                    "discount_amount",
                    "tax_amount",
                    "total_amount",
                ),
                "description": (
                    "Totals are recalculated from order items when the order is saved."
                ),
            },
        ),
        (
            "Internal Notes",
            {
                "fields": ("admin_notes",),
                "description": "Internal notes are only visible in admin.",
            },
        ),
        (
            "System",
            {
                "fields": ("created_at", "updated_at"),
                "classes": ("collapse",),
            },
        ),
    )

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset.prefetch_related(
            "items",
            "items__merch_item",
            "items__ticket_type",
            "items__ticket_type__event",
        )

    @admin.display(ordering="customer_name", description="Customer")
    def customer_summary(self, obj):
        phone = obj.customer_phone or "-"
        return format_html(
            "<strong>{}</strong><br><span>{}</span><br><small>{}</small>",
            obj.customer_name,
            obj.customer_email,
            phone,
        )

    @admin.display(ordering="status", description="Status")
    def status_badge(self, obj):
        tone_map = {
            Order.Status.DRAFT: "neutral",
            Order.Status.PENDING_PAYMENT: "warning",
            Order.Status.PAID: "success",
            Order.Status.CANCELLED: "danger",
            Order.Status.EXPIRED: "neutral",
            Order.Status.REFUNDED: "info",
            Order.Status.PARTIALLY_REFUNDED: "info",
        }
        return render_admin_badge(
            obj.get_status_display(),
            tone_map.get(obj.status, "neutral"),
        )

    @admin.display(description="Inventory")
    def inventory_badge(self, obj):
        if obj.inventory_committed_at:
            return render_admin_badge("Committed", "success")

        if obj.inventory_released_at:
            return render_admin_badge("Released", "warning")

        if obj.status == Order.Status.PAID and not obj.inventory_committed_at:
            return render_admin_badge("Needs attention", "danger")

        return render_admin_badge("Not committed", "neutral")

    @admin.display(description="Items")
    def item_summary(self, obj):
        items = list(obj.items.all())

        if not items:
            return "-"

        first_item = items[0]
        summary = f"{first_item.description} × {first_item.quantity}"

        remaining_count = len(items) - 1
        if remaining_count > 0:
            summary = f"{summary} + {remaining_count} more"

        return summary

    @admin.display(ordering="total_amount", description="Total")
    def total_display(self, obj):
        return f"{obj.currency} {obj.total_amount:.2f}"

    @admin.display(description="Order Summary")
    def order_summary(self, obj):
        if not obj.pk:
            return "Save the order first to view summary."

        item_rows = [
            (
                item.description,
                item.quantity,
                obj.currency,
                item.total_amount,
            )
            for item in obj.items.all()
        ]

        if item_rows:
            item_text = format_html_join(
                "",
                "{} × {} = {} {:.2f}<br>",
                item_rows,
            )
        else:
            item_text = "-"

        if obj.inventory_committed_at:
            inventory_text = "Committed"
        elif obj.inventory_released_at:
            inventory_text = "Released"
        else:
            inventory_text = "Not committed"

        return format_html(
            (
                "<div style='line-height:1.7;'>"
                "<strong>Reference:</strong> {}<br>"
                "<strong>Status:</strong> {}<br>"
                "<strong>Inventory:</strong> {}<br>"
                "<strong>Total:</strong> {} {:.2f}<br>"
                "<strong>Items:</strong><br>{}"
                "</div>"
            ),
            obj.reference_code,
            obj.get_status_display(),
            inventory_text,
            obj.currency,
            obj.total_amount,
            item_text,
        )

    def save_model(self, request, obj, form, change):
        old_status = None
        requested_status = obj.status

        if change and obj.pk:
            old_status = Order.objects.only("status").get(pk=obj.pk).status

        status_changed = (
            change
            and "status" in form.changed_data
            and old_status != requested_status
        )

        if status_changed:
            obj.status = old_status

        super().save_model(request, obj, form, change)

        if status_changed:
            try:
                order, _, inventory_updated = change_order_status(
                    obj.pk,
                    requested_status,
                    created_by=request.user,
                    source="admin_change_form",
                )

                obj.status = order.status

                if inventory_updated:
                    self.message_user(
                        request,
                        "Inventory updated for this order.",
                        level=messages.SUCCESS,
                    )

                if send_order_status_update(order):
                    self.message_user(
                        request,
                        "Customer status update email sent.",
                        level=messages.SUCCESS,
                    )

            except ValidationError as exc:
                self.message_user(
                    request,
                    f"Inventory update failed: {exc}",
                    level=messages.ERROR,
                )

    def save_related(self, request, form, formsets, change):
        super().save_related(request, form, formsets, change)
        form.instance.recalculate_totals(save=True)

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)

        if "admin_notes" in form.base_fields:
            form.base_fields["admin_notes"].widget.attrs["rows"] = 8
            form.base_fields["admin_notes"].help_text = "Visible only in admin."

        if "discount_amount" in form.base_fields:
            form.base_fields["discount_amount"].help_text = (
                "Manual discount amount. Order totals recalculate when saved."
            )

        if "tax_amount" in form.base_fields:
            form.base_fields["tax_amount"].help_text = (
                "Manual tax amount. Order totals recalculate when saved."
            )

        return form


@admin.register(OrderItem)
class OrderItemAdmin(SuperuserDeleteOnlyAdminMixin, TimestampedAdmin):
    list_display = (
        "description",
        "order",
        "quantity",
        "unit_amount",
        "total_amount",
        "created_at",
    )
    list_filter = ("created_at",)
    search_fields = (
        "description",
        "order__reference_code",
        "order__customer_name",
        "order__customer_email",
        "merch_item__name",
        "ticket_type__name",
        "ticket_type__event__title",
    )
    autocomplete_fields = ("order", "merch_item", "ticket_type")
    list_select_related = ("order", "merch_item", "ticket_type")


@admin.register(OrderHistory)
class OrderHistoryAdmin(SuperuserDeleteOnlyAdminMixin, TimestampedAdmin):
    list_display = (
        "order",
        "event_badge",
        "status_transition",
        "short_message",
        "created_by",
        "created_at",
    )
    list_filter = (
        "event_type",
        "from_status",
        "to_status",
        "created_at",
    )
    search_fields = (
        "order__reference_code",
        "order__customer_name",
        "order__customer_email",
        "message",
    )
    readonly_fields = (
        "order",
        "event_type",
        "from_status",
        "to_status",
        "message",
        "metadata",
        "created_by",
        "created_at",
        "updated_at",
    )
    ordering = ("-created_at", "-id")
    list_select_related = ("order", "created_by")

    @admin.display(description="Event")
    def event_badge(self, obj):
        tone_map = {
            OrderHistory.EventType.CREATED: "success",
            OrderHistory.EventType.STATUS_CHANGED: "info",
            OrderHistory.EventType.INVENTORY_COMMITTED: "success",
            OrderHistory.EventType.INVENTORY_RELEASED: "warning",
            OrderHistory.EventType.EMAIL_SENT: "info",
            OrderHistory.EventType.EMAIL_SKIPPED: "neutral",
            OrderHistory.EventType.NOTE: "neutral",
            OrderHistory.EventType.ERROR: "danger",
        }
        return render_admin_badge(
            obj.get_event_type_display(),
            tone_map.get(obj.event_type, "neutral"),
        )

    @admin.display(description="Status")
    def status_transition(self, obj):
        if obj.from_status and obj.to_status:
            return f"{obj.get_from_status_display()} → {obj.get_to_status_display()}"

        if obj.to_status:
            return obj.get_to_status_display()

        return "-"

    @admin.display(description="Message")
    def short_message(self, obj):
        if not obj.message:
            return "-"

        if len(obj.message) <= 80:
            return obj.message

        return f"{obj.message[:77]}..."

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return request.user.is_superuser

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser