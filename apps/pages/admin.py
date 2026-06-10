from django.contrib import admin
from django.http import HttpResponseRedirect
from django.urls import reverse

from apps.core.admin import (
    SuperuserDeleteOnlyAdminMixin,
    TimestampedAdmin,
    make_bulk_update_action,
)
from .selectors import get_site_settings
from .models import PageSection, SiteSettings


make_sections_active = make_bulk_update_action(
    action_name="make_sections_active",
    field_name="is_active",
    value=True,
    description="Mark selected sections as active",
    success_message="{updated} section(s) marked as active.",
)

make_sections_inactive = make_bulk_update_action(
    action_name="make_sections_inactive",
    field_name="is_active",
    value=False,
    description="Mark selected sections as inactive",
    success_message="{updated} section(s) marked as inactive.",
)


@admin.register(SiteSettings)
class SiteSettingsAdmin(SuperuserDeleteOnlyAdminMixin, TimestampedAdmin):
    list_display = ("site_name", "contact_email", "contact_phone", "updated_at")

    fieldsets = (
        ("Brand", {
            "fields": ("site_name", "tagline"),
            "description": "Basic branding and identity shown around the site.",
        }),
        ("Contact Details", {
            "fields": ("contact_email", "contact_phone", "address_text", "google_maps_url"),
            "description": "Public contact and location details.",
        }),
        ("Social Links", {
            "fields": (
                "instagram_url",
                "facebook_url",
                "tiktok_url",
                "youtube_url",
                "whatsapp_url",
            ),
            "description": "Public social and messaging links.",
        }),
        ("System", {
            "fields": ("created_at", "updated_at"),
        }),
    )

    def has_add_permission(self, request):
        if get_site_settings():
            return False
        return super().has_add_permission(request)

    def changelist_view(self, request, extra_context=None):
        obj = get_site_settings()
        if obj:
            url = reverse("admin:pages_sitesettings_change", args=[obj.pk])
            return HttpResponseRedirect(url)
        return super().changelist_view(request, extra_context=extra_context)

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)

        form.base_fields["site_name"].label = "Website name"
        form.base_fields["tagline"].help_text = "Short line shown under the brand name and in metadata."
        form.base_fields["contact_email"].label = "Public email address"
        form.base_fields["contact_phone"].label = "Public phone / WhatsApp"
        form.base_fields["address_text"].label = "Address"
        form.base_fields["address_text"].help_text = "Use line breaks if you want the address to display across multiple lines."
        form.base_fields["google_maps_url"].label = "Google Maps link"
        form.base_fields["google_maps_url"].help_text = "Paste the public map link for the venue."
        form.base_fields["whatsapp_url"].label = "WhatsApp link"
        form.base_fields["whatsapp_url"].help_text = "Use a full wa.me or WhatsApp public link."

        return form


@admin.register(PageSection)
class PageSectionAdmin(SuperuserDeleteOnlyAdminMixin, TimestampedAdmin):
    list_display = (
        "page_key",
        "section_key",
        "title",
        "sort_order",
        "is_active",
        "updated_at",
    )
    list_filter = ("page_key", "is_active")
    search_fields = ("title", "subtitle", "body", "section_key")
    search_help_text = "Search by title, subtitle, body, or section key"
    ordering = ("page_key", "sort_order", "id")
    list_editable = ("sort_order", "is_active")
    actions = [make_sections_active, make_sections_inactive]

    fieldsets = (
        ("Placement", {
            "fields": ("page_key", "section_key"),
            "description": "Controls where this section appears.",
        }),
        ("Text Content", {
            "fields": ("title", "subtitle", "body"),
        }),
        ("Media", {
            "fields": ("image",),
        }),
        ("Call To Action", {
            "fields": ("cta_text", "cta_url"),
        }),
        ("Display", {
            "fields": ("sort_order", "is_active"),
        }),
        ("System", {
            "fields": ("created_at", "updated_at"),
        }),
    )

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)

        form.base_fields["page_key"].label = "Page"
        form.base_fields["page_key"].help_text = "Example: home, about, or contact."
        form.base_fields["section_key"].label = "Section identifier"
        form.base_fields["section_key"].help_text = "Internal identifier for this block. Keep it short and unique per page."
        form.base_fields["sort_order"].label = "Display order"
        form.base_fields["cta_text"].label = "Button text"
        form.base_fields["cta_url"].label = "Button link"

        return form