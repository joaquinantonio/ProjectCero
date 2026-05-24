from django.contrib import admin

from apps.core.admin import (
    SuperuserDeleteOnlyAdminMixin,
    TimestampedAdmin,
    render_admin_badge,
)

from .models import Order, OrderItem


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


@admin.register(Order)
class OrderAdmin(SuperuserDeleteOnlyAdminMixin, TimestampedAdmin):
    list_display = (
        "reference_code",
        "customer_name",
        "customer_email",
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
    inlines = [OrderItemInline]

    readonly_fields = (
        "reference_code",
        "subtotal_amount",
        "total_amount",
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

    def save_related(self, request, form, formsets, change):
        super().save_related(request, form, formsets, change)
        form.instance.recalculate_totals(save=True)


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