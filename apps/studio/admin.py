from django.contrib import admin

from apps.core.admin import (
    AdminImagePreviewMixin,
    SuperuserDeleteOnlyAdminMixin,
    TimestampedAdmin,
    ReadonlyOnChangeAdminMixin,
    basic_fieldset,
    make_bulk_update_action,
)
from .models import StudioService, StudioServiceCategory


make_categories_active = make_bulk_update_action(
    action_name="make_categories_active",
    field_name="is_active",
    value=True,
    description="Mark selected categories as active",
    success_message="{updated} category(ies) marked as active.",
)

make_categories_inactive = make_bulk_update_action(
    action_name="make_categories_inactive",
    field_name="is_active",
    value=False,
    description="Mark selected categories as inactive",
    success_message="{updated} category(ies) marked as inactive.",
)

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


@admin.register(StudioServiceCategory)
class StudioServiceCategoryAdmin(ReadonlyOnChangeAdminMixin, SuperuserDeleteOnlyAdminMixin, TimestampedAdmin):
    list_display = ("name", "slug", "sort_order", "is_active")
    list_filter = ("is_active",)
    search_fields = ("name",)
    search_help_text = "Search categories by name"
    ordering = ("sort_order", "name")
    list_editable = ("sort_order", "is_active")
    actions = [make_categories_active, make_categories_inactive]

    def get_fieldsets(self, request, obj=None):
        basic = basic_fieldset(
            obj,
            ("name", "sort_order", "is_active"),
            new_description=(
                "The slug will be generated automatically from the category name when this category is first created."
            ),
            existing_description=(
                "The slug was generated automatically when this category was created. It is now locked to keep category links stable."
            ),
        )

        return (
            basic,
            ("System", {
                "fields": ("created_at", "updated_at"),
            }),
        )

    readonly_on_change = ("slug",)


@admin.register(StudioService)
class StudioServiceAdmin(ReadonlyOnChangeAdminMixin, AdminImagePreviewMixin, SuperuserDeleteOnlyAdminMixin, TimestampedAdmin):
    image_preview_field = "image"
    readonly_on_change = ("slug",)

    list_display = (
        "name",
        "category",
        "is_featured",
        "is_active",
        "display_order",
        "image_preview",
        "updated_at",
    )
    list_filter = ("category", "is_featured", "is_active")
    search_fields = ("name", "short_description", "description")
    search_help_text = "Search by service name, short description, or description"
    autocomplete_fields = ("category",)
    ordering = ("display_order", "name")
    list_select_related = ("category",)
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
            ("category", "name", "is_active", "is_featured"),
            new_description=(
                "The slug will be generated automatically from the service name when this service is first created."
            ),
            existing_description=(
                "The slug was generated automatically when this service was created. It is now locked to keep service links stable."
            ),
        )

        return (
            basic,
            ("Content", {
                "fields": ("short_description", "description", "image"),
            }),
            ("Commercial", {
                "fields": ("price_text", "duration_text", "display_order"),
            }),
            ("System", {
                "fields": ("created_at", "updated_at"),
            }),
        )

    # readonly fields on change are handled by ReadonlyOnChangeAdminMixin
