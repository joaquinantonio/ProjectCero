from django.contrib import admin
from django.db.models import Count
from django.shortcuts import redirect

from apps.core.admin import (
    ReadonlyOnChangeAdminMixin,
    SuperuserDeleteOnlyAdminMixin,
    TimestampedAdmin,
    make_bulk_update_action,
    render_admin_badge,
)

from .models import Booking, BookingRequest, BookingResource, ScheduleCalendar


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

mark_closed = make_bulk_update_action(
    action_name="mark_closed",
    field_name="status",
    value=BookingRequest.Status.CLOSED,
    description="Mark selected requests as Closed",
    success_message="{updated} request(s) marked as Closed.",
)


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


@admin.register(Booking)
class BookingAdmin(
    SuperuserDeleteOnlyAdminMixin,
    TimestampedAdmin,
):
    list_display = (
        "reference_code",
        "display_title",
        "booking_type_badge",
        "resource",
        "schedule_window",
        "status_badge",
        "request",
        "created_at",
    )
    list_filter = (
        "booking_type",
        "resource",
        "status",
        "scheduled_start_at",
        "created_at",
    )
    search_fields = (
        "reference_code",
        "title",
        "request__reference_code",
        "request__name",
        "request__email",
        "request__phone",
        "internal_notes",
    )
    search_help_text = (
        "Search by booking reference, title, request reference, customer name, "
        "email, phone, or notes"
    )
    autocomplete_fields = (
        "request",
        "resource",
    )
    list_select_related = (
        "request",
        "resource",
    )
    ordering = ("scheduled_start_at",)
    date_hierarchy = "scheduled_start_at"

    readonly_fields = (
        "reference_code",
        "created_at",
        "updated_at",
    )

    fieldsets = (
        (
            "Booking",
            {
                "fields": (
                    "reference_code",
                    "title",
                    "booking_type",
                    "status",
                    "resource",
                    "request",
                ),
            },
        ),
        (
            "Schedule",
            {
                "fields": (
                    "scheduled_start_at",
                    "scheduled_end_at",
                ),
                "description": (
                    "These fields control the admin and public availability calendars."
                ),
            },
        ),
        (
            "Internal Notes",
            {
                "fields": ("internal_notes",),
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

    @admin.display(ordering="booking_type", description="Type")
    def booking_type_badge(self, obj):
        tone_map = {
            Booking.BookingType.STUDIO: "accent",
            Booking.BookingType.VENUE: "info",
        }
        return render_admin_badge(
            obj.get_booking_type_display(),
            tone_map.get(obj.booking_type, "neutral"),
        )

    @admin.display(ordering="status", description="Status")
    def status_badge(self, obj):
        tone_map = {
            Booking.Status.TENTATIVE: "warning",
            Booking.Status.CONFIRMED: "success",
            Booking.Status.CANCELLED: "danger",
            Booking.Status.COMPLETED: "neutral",
            Booking.Status.NO_SHOW: "danger",
        }
        return render_admin_badge(
            obj.get_status_display(),
            tone_map.get(obj.status, "neutral"),
        )

    @admin.display(description="Scheduled")
    def schedule_window(self, obj):
        return (
            f"{obj.scheduled_start_at:%d %b %Y, %I:%M %p} – "
            f"{obj.scheduled_end_at:%I:%M %p}"
        )

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)

        if "internal_notes" in form.base_fields:
            form.base_fields["internal_notes"].widget.attrs["rows"] = 8
            form.base_fields["internal_notes"].help_text = "Visible only in admin."

        if "request" in form.base_fields:
            form.base_fields["request"].help_text = (
                "Optional. Link this booking to the original public request."
            )

        if "resource" in form.base_fields:
            form.base_fields["resource"].help_text = (
                "For now this should usually be CeroPJ Venue."
            )

        return form


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
        "booking_count",
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
    actions = [mark_in_review, mark_contacted, mark_closed]
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

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset.annotate(bookings_total=Count("bookings"))

    def has_add_permission(self, request):
        return request.user.is_superuser

    @admin.display(ordering="request_type", description="Type")
    def request_type_badge(self, obj):
        tone_map = {
            BookingRequest.RequestType.GENERAL: "neutral",
            BookingRequest.RequestType.STUDIO: "accent",
            BookingRequest.RequestType.VENUE: "info",
        }
        return render_admin_badge(
            obj.get_request_type_display(),
            tone_map.get(obj.request_type, "neutral"),
        )

    @admin.display(description="Bookings")
    def booking_count(self, obj):
        return obj.bookings_total

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
                    "description": (
                        "Update the request status and internal notes here. "
                        "Confirmed calendar blocks are now managed through Booking records."
                    ),
                },
            ),
            (
                "Requester Details",
                {
                    "fields": (("name", "email"), "phone"),
                },
            ),
            (
                "Request Details",
                {
                    "fields": (
                        "request_type",
                        "event",
                        ("preferred_date", "preferred_time"),
                        "guest_count",
                    ),
                    "description": (
                        "Submitted customer request details. Create a Booking "
                        "record when the date/time is confirmed internally."
                    ),
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
            form.base_fields["status"].help_text = (
                "Use this to track the request as it moves through your workflow."
            )

        if "admin_notes" in form.base_fields:
            form.base_fields["admin_notes"].label = "Internal notes"
            form.base_fields["admin_notes"].help_text = "Visible only in admin."
            form.base_fields["admin_notes"].widget.attrs["rows"] = 8

        if "event" in form.base_fields:
            form.base_fields["event"].label = "Related event"
            form.base_fields["event"].help_text = (
                "Optional. Link this request to a specific event if relevant."
            )

        if "message" in form.base_fields:
            form.base_fields["message"].label = "Submitted message"
            form.base_fields["message"].widget.attrs["rows"] = 6

        return form


@admin.register(ScheduleCalendar)
class ScheduleCalendarAdmin(admin.ModelAdmin):
    def changelist_view(self, request, extra_context=None):
        return redirect("admin:schedule_calendar")

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return (
            request.user.is_superuser
            or request.user.has_perm("bookings.view_bookingrequest")
            or request.user.has_perm("bookings.view_booking")
            or request.user.has_perm("events.view_event")
        )

    def has_delete_permission(self, request, obj=None):
        return False

    def has_view_permission(self, request, obj=None):
        return (
            request.user.is_superuser
            or request.user.has_perm("bookings.view_bookingrequest")
            or request.user.has_perm("bookings.view_booking")
            or request.user.has_perm("events.view_event")
        )