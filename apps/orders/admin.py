from django.contrib import admin
from django.contrib import messages
from django.core.exceptions import ValidationError

from apps.core.admin import (
    SuperuserDeleteOnlyAdminMixin,
    TimestampedAdmin,
    render_admin_badge,
)

from .models import Order, OrderHistory, OrderItem
from .services import send_order_status_update
from .workflow import change_order_status


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 1
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
    fields = (
        "created_at",
        "event_type",
        "from_status",
        "to_status",
        "message",
        "created_by",
    )
    readonly_fields = fields
    ordering = ("-created_at", "-id")

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
        "customer_name",
        "customer_email",
        "customer_phone",
        "status_badge",
        "currency",
        "total_amount",
        "created_at",
    )
    list_filter = ("status", "currency", "created_at")
    search_fields = (
        "reference_code",
        "customer_name",
        "customer_email",
        "customer_phone",
        "admin_notes",
    )
    ordering = ("-created_at",)
    date_hierarchy = "created_at"
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
        "subtotal_amount",
        "total_amount",
        "inventory_committed_at",
        "inventory_released_at",
        "created_at",
        "updated_at",
    )

    fieldsets = (
        (
            "Customer",
            {
                "fields": (
                    "reference_code",
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
                    "Inventory is committed when the order becomes Paid. "
                    "Committed inventory is released when the order becomes Cancelled, Expired, or Refunded."
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
            },
        ),
        (
            "Internal Notes",
            {
                "fields": ("admin_notes",),
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
        "event_type",
        "from_status",
        "to_status",
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

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return request.user.is_superuser

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser