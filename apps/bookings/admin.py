from django.contrib import admin

from apps.core.admin import SuperuserDeleteOnlyAdminMixin, TimestampedAdmin, ReadonlyOnChangeAdminMixin, make_bulk_update_action
from .models import BookingRequest


mark_in_review = make_bulk_update_action(
    action_name="mark_in_review",
    field_name="status",
    value=BookingRequest.Status.IN_REVIEW,
    description="Mark selected requests as In Review",
    success_message="{updated} request(s) marked as In Review.",
)

mark_contacted = make_bulk_update_action(
    action_name="mark_contacted",
    field_name="status",
    value=BookingRequest.Status.CONTACTED,
    description="Mark selected requests as Contacted",
    success_message="{updated} request(s) marked as Contacted.",
)

mark_confirmed = make_bulk_update_action(
    action_name="mark_confirmed",
    field_name="status",
    value=BookingRequest.Status.CONFIRMED,
    description="Mark selected requests as Confirmed",
    success_message="{updated} request(s) marked as Confirmed.",
)

mark_closed = make_bulk_update_action(
    action_name="mark_closed",
    field_name="status",
    value=BookingRequest.Status.CLOSED,
    description="Mark selected requests as Closed",
    success_message="{updated} request(s) marked as Closed.",
)


@admin.register(BookingRequest)
class BookingRequestAdmin(ReadonlyOnChangeAdminMixin, SuperuserDeleteOnlyAdminMixin, TimestampedAdmin):
    list_display = (
        "reference_code",
        "name",
        "request_type",
        "email",
        "preferred_date",
        "status",
        "created_at",
    )
    list_filter = ("request_type", "status", "created_at")
    search_fields = (
        "reference_code",
        "name",
        "email",
        "phone",
        "message",
        "admin_notes",
    )
    search_help_text = "Search by reference, name, email, phone, message, or admin notes"
    autocomplete_fields = ("event",)
    ordering = ("-created_at",)
    date_hierarchy = "created_at"
    actions = [mark_in_review, mark_contacted, mark_confirmed, mark_closed]
    list_select_related = ("event",)

    fieldsets = (
        ("Request Summary", {
            "fields": ("reference_code", "request_type", "status"),
        }),
        ("Requester Details", {
            "fields": ("name", "email", "phone"),
        }),
        ("Booking Details", {
            "fields": ("event", "preferred_date", "preferred_time", "guest_count"),
        }),
        ("Message", {
            "fields": ("message",),
        }),
        ("Internal Notes", {
            "fields": ("admin_notes",),
        }),
        ("System", {
            "fields": ("created_at", "updated_at"),
        }),
    )

    readonly_fields = ("reference_code", "created_at", "updated_at")
    readonly_on_change = ("request_type", "name", "email", "phone", "message")

    # Disable adding booking request from admin. Not necessary as requests originate from external parties
    # However, still allow admin to add manually for edge cases such as phone requests, walk-ins, or to create test data, so only admins can add.
    def has_add_permission(self, request):
        return request.user.is_superuser

    # readonly fields on change are handled by ReadonlyOnChangeAdminMixin

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)

        if "event" in form.base_fields:
            form.base_fields["event"].label = "Related event"
            form.base_fields["event"].help_text = "Optional. Link this request to a specific event if relevant."

        if "admin_notes" in form.base_fields:
            form.base_fields["admin_notes"].label = "Internal notes"
            form.base_fields["admin_notes"].help_text = "Visible only in admin."

        return form