from django.contrib import admin

from apps.core.admin import (
    AdminImagePreviewMixin,
    SuperuserDeleteOnlyAdminMixin,
    TimestampedAdmin,
    ReadonlyOnChangeAdminMixin,
    basic_fieldset,
    make_bulk_update_action,
)
from .models import Artist


make_active = make_bulk_update_action(
    action_name="make_active",
    field_name="is_active",
    value=True,
    description="Mark selected artists as active",
    success_message="{updated} artist(s) marked as active.",
)

make_inactive = make_bulk_update_action(
    action_name="make_inactive",
    field_name="is_active",
    value=False,
    description="Mark selected artists as inactive",
    success_message="{updated} artist(s) marked as inactive.",
)

make_featured = make_bulk_update_action(
    action_name="make_featured",
    field_name="is_featured",
    value=True,
    description="Mark selected artists as featured",
    success_message="{updated} artist(s) marked as featured.",
)

make_not_featured = make_bulk_update_action(
    action_name="make_not_featured",
    field_name="is_featured",
    value=False,
    description="Remove featured status from selected artists",
    success_message="{updated} artist(s) unfeatured.",
)


@admin.register(Artist)
class ArtistAdmin(ReadonlyOnChangeAdminMixin, AdminImagePreviewMixin, SuperuserDeleteOnlyAdminMixin, TimestampedAdmin):
    image_preview_field = "image"
    readonly_on_change = ("slug",)

    list_display = (
        "name",
        "artist_type",
        "is_featured",
        "feature_order",
        "image_preview",
        "is_active",
        "updated_at",
    )
    list_filter = ("artist_type", "is_featured", "is_active")
    search_fields = ("name", "short_bio", "bio")
    search_help_text = "Search by artist name, short bio, or full bio"
    ordering = ("feature_order", "name")
    list_editable = ("is_featured", "feature_order", "is_active")
    actions = [make_active, make_inactive, make_featured, make_not_featured]

    def get_fieldsets(self, request, obj=None):
        basic = basic_fieldset(
            obj,
            ("name", "artist_type", "is_active"),
            new_description="The slug will be generated automatically from the artist name when this artist is first created.",
            existing_description=(
                "The slug was generated automatically when this artist was created. It is now locked to keep artist page links stable."
            ),
        )

        return (
            basic,
            ("Featured Display", {
                "fields": ("is_featured", "feature_order", "short_bio"),
                "description": "Use this to control whether the artist appears in featured areas and in what order.",
            }),
            ("Profile", {
                "fields": ("bio", "image"),
            }),
            ("Links", {
                "fields": ("instagram_url", "spotify_url", "youtube_url"),
            }),
            ("System", {
                "fields": ("created_at", "updated_at"),
            }),
        )

    # readonly fields on change are handled by ReadonlyOnChangeAdminMixin

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)

        if "short_bio" in form.base_fields:
            form.base_fields["short_bio"].label = "Short summary"
            form.base_fields["short_bio"].help_text = "Short public summary shown on listings and previews."

        if "feature_order" in form.base_fields:
            form.base_fields["feature_order"].label = "Featured display order"
            form.base_fields["feature_order"].help_text = "Lower numbers appear first."

        if "bio" in form.base_fields:
            form.base_fields["bio"].help_text = "Full public artist profile."

        return form