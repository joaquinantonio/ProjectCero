from django.contrib import admin

from apps.core.admin import (
    AdminImagePreviewMixin,
    SuperuserDeleteOnlyAdminMixin,
    TimestampedAdmin,
    ReadonlyOnChangeAdminMixin,
    basic_fieldset,
    make_bulk_update_action,
)
from .models import StudioService, Equipment


make_services_active = make_bulk_update_action(
    action_name="make_services_active",
    field_name="is_active",
    value=True,
    description="Mark selected services as active",
    success_message="{updated} service(s) marked as active.",
)

make_services_inactive = make_bulk_update_action(
    action_name="make_services_inactive",
    field_name="is_active",
    value=False,
    description="Mark selected services as inactive",
    success_message="{updated} service(s) marked as inactive.",
)

make_services_featured = make_bulk_update_action(
    action_name="make_services_featured",
    field_name="is_featured",
    value=True,
    description="Mark selected services as featured",
    success_message="{updated} service(s) marked as featured.",
)

make_services_not_featured = make_bulk_update_action(
    action_name="make_services_not_featured",
    field_name="is_featured",
    value=False,
    description="Remove featured status from selected services",
    success_message="{updated} service(s) unfeatured.",
)


make_equipment_active = make_bulk_update_action(
    action_name="make_equipment_active",
    field_name="is_active",
    value=True,
    description="Mark selected equipment as active",
    success_message="{updated} equipment item(s) marked as active.",
)

make_equipment_inactive = make_bulk_update_action(
    action_name="make_equipment_inactive",
    field_name="is_active",
    value=False,
    description="Mark selected equipment as inactive",
    success_message="{updated} equipment item(s) marked as inactive.",
)


@admin.register(StudioService)
class StudioServiceAdmin(
    ReadonlyOnChangeAdminMixin,
    AdminImagePreviewMixin,
    SuperuserDeleteOnlyAdminMixin,
    TimestampedAdmin,
):
    image_preview_field = "image"
    readonly_on_change = ("slug",)

    list_display = (
        "name",
        "is_featured",
        "is_active",
        "display_order",
        "image_preview",
        "updated_at",
    )
    list_filter = ("is_featured", "is_active")
    search_fields = ("name", "short_description", "description")
    search_help_text = "Search by service name, short description, or description"
    ordering = ("display_order", "name")
    list_editable = ("is_featured", "is_active", "display_order")
    actions = [
        make_services_active,
        make_services_inactive,
        make_services_featured,
        make_services_not_featured,
    ]

    def get_fieldsets(self, request, obj=None):
        basic = basic_fieldset(
            obj,
            ("name", "is_active", "is_featured"),
            new_description=(
                "The slug will be generated automatically from the service name "
                "when this service is first created."
            ),
            existing_description=(
                "The slug was generated automatically when this service was created. "
                "It is now locked to keep service links stable."
            ),
        )

        return (
            basic,
            (
                "Content",
                {
                    "fields": ("short_description", "description", "image"),
                },
            ),
            (
                "Commercial",
                {
                    "fields": ("price_text", "duration_text", "display_order"),
                },
            ),
            (
                "System",
                {
                    "fields": ("created_at", "updated_at"),
                },
            ),
        )


@admin.register(Equipment)
class EquipmentAdmin(SuperuserDeleteOnlyAdminMixin, TimestampedAdmin):
    list_display = ("name", "category", "quantity", "is_active", "updated_at")
    list_filter = ("category", "is_active")
    search_fields = ("name", "category", "description")
    search_help_text = "Search by equipment name, category, or description"
    ordering = ("name",)
    list_editable = ("is_active",)
    actions = [make_equipment_active, make_equipment_inactive]

    fieldsets = (
        (
            "Equipment Details",
            {
                "fields": ("name", "category", "quantity", "is_active"),
            },
        ),
        (
            "Description",
            {
                "fields": ("description",),
            },
        ),
        (
            "System",
            {
                "fields": ("created_at", "updated_at"),
            },
        ),
    )
