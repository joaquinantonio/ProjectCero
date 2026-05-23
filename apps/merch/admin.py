from django.contrib import admin

from apps.core.admin import (
    AdminImagePreviewMixin,
    SuperuserDeleteOnlyAdminMixin,
    TimestampedAdmin,
    render_boolean_badge,
)
from .models import MerchItem


@admin.action(description="Mark selected merch as active")
def make_active(modeladmin, request, queryset):
    updated = queryset.update(is_active=True)
    modeladmin.message_user(request, f"{updated} merch item(s) marked as active.")


@admin.action(description="Mark selected merch as inactive")
def make_inactive(modeladmin, request, queryset):
    updated = queryset.update(is_active=False)
    modeladmin.message_user(request, f"{updated} merch item(s) marked as inactive.")


@admin.action(description="Mark selected merch as featured")
def make_featured(modeladmin, request, queryset):
    updated = queryset.update(is_featured=True)
    modeladmin.message_user(request, f"{updated} merch item(s) marked as featured.")


@admin.action(description="Remove featured status from selected merch")
def make_unfeatured(modeladmin, request, queryset):
    updated = queryset.update(is_featured=False)
    modeladmin.message_user(request, f"{updated} merch item(s) unfeatured.")


@admin.register(MerchItem)
class MerchItemAdmin(AdminImagePreviewMixin, SuperuserDeleteOnlyAdminMixin, TimestampedAdmin):
    image_preview_field = "image"

    list_display = (
        "name",
        "price_text",
        "availability_text",
        "featured_badge",
        "active_badge",
        "display_order",
        "image_preview",
        "updated_at",
    )

    list_editable = (
        # "is_featured",
        # "is_active",
        "display_order",)
    list_filter = ("is_active", "is_featured")
    search_fields = ("name", "short_description", "description", "price_text", "availability_text")
    search_help_text = "Search by name, description, price text, or availability"
    ordering = ("display_order", "name")

    actions = [make_active, make_inactive, make_featured, make_unfeatured]

    def get_fieldsets(self, request, obj=None):
        if obj:
            return (
                ("Basic", {
                    "fields": ("name", "slug", "is_active", "is_featured"),
                    "description": "The slug was generated automatically when this merch item was created. It is now locked to keep merch links stable.",
                }),
                ("Content", {
                    "fields": ("short_description", "description", "image"),
                }),
                ("Commercial", {
                    "fields": ("price_text", "availability_text", "display_order"),
                }),
                ("Call To Action", {
                    "fields": ("cta_text", "cta_url"),
                }),
                ("System", {
                    "fields": ("created_at", "updated_at"),
                }),
            )

        return (
            ("Basic", {
                "fields": ("name", "is_active", "is_featured"),
                "description": "The slug will be generated automatically from the merch item name when it is first created.",
            }),
            ("Content", {
                "fields": ("short_description", "description", "image"),
            }),
            ("Commercial", {
                "fields": ("price_text", "availability_text", "display_order"),
            }),
            ("Call To Action", {
                "fields": ("cta_text", "cta_url"),
            }),
            ("System", {
                "fields": ("created_at", "updated_at"),
            }),
        )

    def get_readonly_fields(self, request, obj=None):
        readonly = list(super().get_readonly_fields(request, obj))
        if obj:
            readonly.append("slug")
        return tuple(readonly)

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)

        if "short_description" in form.base_fields:
            form.base_fields["short_description"].label = "Short summary"
            form.base_fields["short_description"].help_text = "Short public summary shown on the merch listing."

        if "description" in form.base_fields:
            form.base_fields["description"].help_text = "Full public merch description."

        if "price_text" in form.base_fields:
            form.base_fields["price_text"].label = "Displayed price"

        if "availability_text" in form.base_fields:
            form.base_fields["availability_text"].label = "Availability note"

        if "display_order" in form.base_fields:
            form.base_fields["display_order"].label = "Display order"
            form.base_fields["display_order"].help_text = "Lower numbers appear first."

        if "cta_text" in form.base_fields:
            form.base_fields["cta_text"].label = "Button text"

        if "cta_url" in form.base_fields:
            form.base_fields["cta_url"].label = "Button link"

        return form

    @admin.display(ordering="is_featured", description="Featured")
    def featured_badge(self, obj):
        return render_boolean_badge(
            obj.is_featured,
            true_label="Featured",
            false_label="Standard",
            true_tone="accent",
            false_tone="neutral",
        )

    @admin.display(ordering="is_active", description="Active")
    def active_badge(self, obj):
        return render_boolean_badge(
            obj.is_active,
            true_label="Active",
            false_label="Hidden",
            true_tone="success",
            false_tone="danger",
        )