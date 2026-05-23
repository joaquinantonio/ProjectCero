from django.contrib import admin
from django.utils import timezone

from apps.core.admin import (
    AdminImagePreviewMixin,
    SuperuserDeleteOnlyAdminMixin,
    TimestampedAdmin,
    ReadonlyOnChangeAdminMixin,
    basic_fieldset,
    make_bulk_update_action,
    render_admin_badge,
    render_boolean_badge,
)
from .models import Event, EventArtist, EventCategory


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


@admin.action(description="Mark selected events as Published")
def make_published(modeladmin, request, queryset):
    updated = 0
    for event in queryset:
        if event.status != Event.Status.PUBLISHED:
            event.status = Event.Status.PUBLISHED
            if not event.published_at:
                event.published_at = timezone.now()
            event.save(update_fields={"status", "published_at"})
            updated += 1
    modeladmin.message_user(request, f"{updated} event(s) marked as Published.")


make_draft = make_bulk_update_action(
    action_name="make_draft",
    field_name="status",
    value=Event.Status.DRAFT,
    description="Mark selected events as Draft",
    success_message="{updated} event(s) marked as Draft.",
)

make_featured = make_bulk_update_action(
    action_name="make_featured",
    field_name="is_featured",
    value=True,
    description="Feature selected events",
    success_message="{updated} event(s) marked as Featured.",
)

make_unfeatured = make_bulk_update_action(
    action_name="make_unfeatured",
    field_name="is_featured",
    value=False,
    description="Unfeature selected events",
    success_message="{updated} event(s) unfeatured.",
)


@admin.register(EventCategory)
class EventCategoryAdmin(ReadonlyOnChangeAdminMixin, SuperuserDeleteOnlyAdminMixin, TimestampedAdmin):
    list_display = ("name", "slug", "sort_order", "is_active")
    list_filter = ("is_active",)
    search_fields = ("name", "description")
    search_help_text = "Search categories by name or description"
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
            ("Content", {
                "fields": ("description",),
            }),
            ("System", {
                "fields": ("created_at", "updated_at"),
            }),
        )

    readonly_on_change = ("slug",)


class EventArtistInline(admin.TabularInline):
    model = EventArtist
    extra = 1
    autocomplete_fields = ("artist",)
    fields = ("artist", "role_name", "sort_order")
    ordering = ("sort_order", "id")


@admin.register(Event)
class EventAdmin(ReadonlyOnChangeAdminMixin, AdminImagePreviewMixin, SuperuserDeleteOnlyAdminMixin, TimestampedAdmin):
    image_preview_field = "poster"
    readonly_on_change = ("slug", "published_at")

    list_display = (
        "title",
        "category",
        "start_at",
        "status_badge",
        "featured_badge",
        "image_preview",
        "updated_at",
    )
    list_filter = ("status", "is_featured", "category", "start_at")
    search_fields = ("title", "short_description", "description", "location_text", "time_note")
    search_help_text = "Search by title, short summary, description, location, or timing note"
    autocomplete_fields = ("category",)
    inlines = [EventArtistInline]
    ordering = ("start_at", "title")
    date_hierarchy = "start_at"
    list_select_related = ("category",)
    actions = [make_published, make_draft, make_featured, make_unfeatured]

    def get_fieldsets(self, request, obj=None):
        basic = basic_fieldset(
            obj,
            ("category", "title", "status", "is_featured"),
            new_description=(
                "The slug will be generated automatically from the event title when this event is first created."
            ),
            existing_description=(
                "The slug was generated automatically when this event was created. It is now locked to keep event links stable."
            ),
        )

        # Note: published_at is included in the change view via ReadonlyOnChangeAdminMixin
        return (
            basic,
            ("Content", {
                "fields": ("short_description", "description", "poster"),
            }),
            ("Schedule", {
                "fields": ("start_at", "end_at", "time_note") if not obj else ("start_at", "end_at", "time_note", "published_at"),
                "description": "End time is optional. Use Timing note for human-friendly text like '10 PM until late'.",
            }),
            ("Venue / Sales", {
                "fields": ("location_text", "ticket_url", "price_text"),
            }),
            ("System", {
                "fields": ("created_at", "updated_at"),
            }),
        )

    # readonly fields on change are handled by ReadonlyOnChangeAdminMixin

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)

        if "short_description" in form.base_fields:
            form.base_fields["short_description"].label = "Short summary"
            form.base_fields["short_description"].help_text = "Used on cards, previews, and metadata."

        if "end_at" in form.base_fields:
            form.base_fields["end_at"].required = False
            form.base_fields["end_at"].help_text = "Optional. Leave blank if the event does not have a fixed end time."

        if "time_note" in form.base_fields:
            form.base_fields["time_note"].label = "Timing note"
            form.base_fields["time_note"].help_text = "Optional public-facing text, e.g. '10 PM until late' or '8 PM onwards'."

        if "ticket_url" in form.base_fields:
            form.base_fields["ticket_url"].label = "Tickets / RSVP link"

        if "price_text" in form.base_fields:
            form.base_fields["price_text"].label = "Displayed price"

        return form

    @admin.display(ordering="status", description="Status")
    def status_badge(self, obj):
        tone_map = {
            Event.Status.DRAFT: "neutral",
            Event.Status.PUBLISHED: "success",
            Event.Status.CANCELLED: "danger",
        }
        return render_admin_badge(
            obj.get_status_display(),
            tone_map.get(obj.status, "neutral"),
        )

    @admin.display(ordering="is_featured", description="Featured")
    def featured_badge(self, obj):
        return render_boolean_badge(
            obj.is_featured,
            true_label="Featured",
            false_label="Standard",
            true_tone="accent",
            false_tone="neutral",
        )