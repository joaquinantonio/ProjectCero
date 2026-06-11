from django.contrib import admin

from apps.core.admin import (
    SuperuserDeleteOnlyAdminMixin,
    TimestampedAdmin,
)

from .models import BookingResource


@admin.register(BookingResource)
class BookingResourceAdmin(
    SuperuserDeleteOnlyAdminMixin,
    TimestampedAdmin,
):
    list_display = (
        "name",
        "is_active",
        "display_order",
        "updated_at",
    )
    list_filter = ("is_active",)
    search_fields = ("name", "description")
    prepopulated_fields = {"slug": ("name",)}
    ordering = ("display_order", "name")