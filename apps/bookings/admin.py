from django.contrib import admin

from apps.core.admin import (
    ReadonlyOnChangeAdminMixin,
    SuperuserDeleteOnlyAdminMixin,
    TimestampedAdmin,
    make_bulk_update_action,
    render_admin_badge,
)
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
class BookingRequestAdmin(
    ReadonlyOnChangeAdminMixin,
    SuperuserDeleteOnlyAdminMixin,
    TimestampedAdmin,
):
    list_display = (
        "reference_code",
        "name",
        "request_type_badge",
        "email",
        "preferred_date",
        "status_badge",
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

    readonly_fields = ("reference_code", "created_at", "updated_at")
    readonly_on_change = (
        "request_type",
        "name",
        "email",
        "phone",
        "preferred_date",
        "preferred_time",
        "guest_count",
        "message",
    )

    def has_add_permission(self, request):
        return request.user.is_superuser

    @admin.display(ordering="request_type", description="Type")
    def request_type_badge(self, obj):
        tone_map = {
            BookingRequest.RequestType.GENERAL: "neutral",
            BookingRequest.RequestType.STUDIO: "accent",
            BookingRequest.RequestType.VENUE: "info",
            BookingRequest.RequestType.PRIVATE_EVENT: "warning",
        }
        return render_admin_badge(
            obj.get_request_type_display(),
            tone_map.get(obj.request_type, "neutral"),
        )

    @admin.display(ordering="status", description="Status")
    def status_badge(self, obj):
        tone_map = {
            BookingRequest.Status.NEW: "warning",
            BookingRequest.Status.IN_REVIEW: "info",
            BookingRequest.Status.CONTACTED: "accent",
            BookingRequest.Status.CONFIRMED: "success",
            BookingRequest.Status.CLOSED: "neutral",
            BookingRequest.Status.CANCELLED: "danger",
        }
        return render_admin_badge(
            obj.get_status_display(),
            tone_map.get(obj.status, "neutral"),
        )

    def get_fieldsets(self, request, obj=None):
        workflow_fields = ("status", "admin_notes")
        if obj:
            workflow_fields = ("reference_code", "status", "admin_notes")

        return (
            (
                "Workflow",
                {
                    "fields": workflow_fields,
                    "classes": ("wide", "workflow-panel"),
                    "description": "Update the status and internal notes here. The original requester details are shown below.",
                },
            ),
            (
                "Requester Details",
                {
                    "fields": (("name", "email"), "phone"),
                },
            ),
            (
                "Booking Details",
                {
                    "fields": ("request_type", "event", ("preferred_date", "preferred_time"), "guest_count"),
                    "description": "Submitted booking details. You can link a related event internally if needed.",
                },
            ),
            (
                "Submitted Message",
                {
                    "fields": ("message",),
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

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)

        if "status" in form.base_fields:
            form.base_fields["status"].help_text = "Use this to track the request as it moves through your workflow."

        if "admin_notes" in form.base_fields:
            form.base_fields["admin_notes"].label = "Internal notes"
            form.base_fields["admin_notes"].help_text = "Visible only in admin."
            form.base_fields["admin_notes"].widget.attrs["rows"] = 8

        if "event" in form.base_fields:
            form.base_fields["event"].label = "Related event"
            form.base_fields["event"].help_text = "Optional. Link this request to a specific event if relevant."

        if "message" in form.base_fields:
            form.base_fields["message"].label = "Submitted message"
            form.base_fields["message"].widget.attrs["rows"] = 6

        return form