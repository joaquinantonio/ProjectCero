from django.contrib import admin
from django.db.models import Count
from django.urls import reverse
from django.utils import timezone
from django.utils.html import format_html, format_html_join
from django.utils.http import urlencode

from apps.core.admin import (
    ReadonlyOnChangeAdminMixin,
    SuperuserDeleteOnlyAdminMixin,
    TimestampedAdmin,
    render_admin_badge,
)

from .admin_actions import (
    mark_cancelled,
    mark_closed,
    mark_contacted,
    mark_in_review,
)
from .admin_filters import BookingRequestCalendarStatusFilter
from .models import BookingRequest


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
        "calendar_status",
        "status_badge",
        "created_at",
        "create_booking_link",
    )
    list_filter = (
        BookingRequestCalendarStatusFilter,
        "request_type",
        "status",
        "created_at",
    )
    search_fields = (
        "reference_code",
        "name",
        "email",
        "phone",
        "message",
        "admin_notes",
    )
    search_help_text = "Search by reference, name, email, phone, message, or admin notes."
    autocomplete_fields = ("event",)
    ordering = ("-created_at",)
    date_hierarchy = "created_at"
    actions = [
        mark_in_review,
        mark_contacted,
        mark_closed,
        mark_cancelled,
    ]
    list_select_related = ("event",)

    readonly_fields = (
        "reference_code",
        "calendar_booking_link",
        "created_at",
        "updated_at",
    )
    readonly_on_change = (
        "request_type",
        "name",
        "email",
        "phone",
        "preferred_date",
        "preferred_start_time",
        "preferred_end_time",
        "guest_count",
        "message",
    )

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset.annotate(bookings_total=Count("bookings"))

    def has_add_permission(self, request):
        return request.user.is_superuser

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)

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

    @admin.display(description="Calendar")
    def calendar_status(self, obj):
        count = getattr(obj, "bookings_total", None)
        if count is None:
            count = obj.bookings.count()

        if count:
            label = f"{count} booking" if count == 1 else f"{count} bookings"
            return render_admin_badge(label, "success")

        if obj.status == BookingRequest.Status.CONVERTED:
            return render_admin_badge("Booking missing", "danger")

        return render_admin_badge("No booking", "neutral")

    @admin.display(description="Calendar Action")
    def create_booking_link(self, obj):
        if not obj.pk:
            return "-"

        if obj.bookings.exists():
            booking = obj.bookings.order_by("scheduled_start_at", "id").first()
            url = reverse("admin:bookings_booking_change", args=[booking.pk])
            return format_html('<a href="{}">Open booking</a>', url)

        if obj.request_type not in (
            BookingRequest.RequestType.STUDIO,
            BookingRequest.RequestType.VENUE,
        ):
            return "-"

        if not (
            obj.preferred_date
            and obj.preferred_start_time
            and obj.preferred_end_time
        ):
            return render_admin_badge("Need date/time", "warning")

        url = reverse("admin:bookings_booking_add")
        params = urlencode({"request": obj.pk})
        return format_html('<a href="{}?{}">Create booking</a>', url, params)

    @admin.display(description="Calendar booking")
    def calendar_booking_link(self, obj):
        if not obj or not obj.pk:
            return "Save this request first."

        if obj.bookings.exists():
            rows = []

            for booking in obj.bookings.order_by("scheduled_start_at", "id"):
                url = reverse("admin:bookings_booking_change", args=[booking.pk])
                start_at = timezone.localtime(booking.scheduled_start_at)
                end_at = timezone.localtime(booking.scheduled_end_at)

                rows.append(
                    (
                        url,
                        booking.reference_code,
                        booking.get_booking_type_display(),
                        f"{start_at:%d %b %Y, %I:%M %p}",
                        f"{end_at:%I:%M %p}",
                    )
                )

            return format_html_join(
                "",
                '<p><a class="button" href="{}">Open {}</a> '
                '<span class="help">{} · {} to {}</span></p>',
                rows,
            )

        if obj.request_type not in (
            BookingRequest.RequestType.STUDIO,
            BookingRequest.RequestType.VENUE,
        ):
            return "General enquiries do not create calendar bookings."

        if not (
            obj.preferred_date
            and obj.preferred_start_time
            and obj.preferred_end_time
        ):
            return (
                "Preferred date, start time, and end time are required before "
                "creating a calendar booking."
            )

        url = reverse("admin:bookings_booking_add")
        params = urlencode({"request": obj.pk})
        return format_html(
            '<p><a class="button" href="{}?{}">Create calendar booking</a></p>'
            '<p class="help">This opens a prefilled Booking record. '
            'Saving that Booking is what blocks admin and public calendars.</p>',
            url,
            params,
        )

    def get_fieldsets(self, request, obj=None):
        workflow_fields = ("status", "admin_notes")

        if obj:
            workflow_fields = (
                "reference_code",
                "status",
                "admin_notes",
                "calendar_booking_link",
            )

        return (
            (
                "Workflow",
                {
                    "fields": workflow_fields,
                    "classes": ("wide", "workflow-panel"),
                    "description": (
                        "Update the request status and internal notes here. "
                        "A request only blocks calendars after it has a linked Booking record."
                    ),
                },
            ),
            (
                "Requester Details",
                {
                    "fields": (("name", "email"), "phone"),
                    "description": "Customer contact information submitted with the request.",
                },
            ),
            (
                "Request Details",
                {
                    "fields": (
                        "request_type",
                        "event",
                        ("preferred_date", "preferred_start_time", "preferred_end_time"),
                        "guest_count",
                    ),
                    "description": (
                        "Customer's preferred timing and type. These are locked after initial submission. "
                        "Create a calendar booking once you confirm the details."
                    ),
                },
            ),
            (
                "Submitted Message",
                {
                    "fields": ("message",),
                    "classes": ("wide",),
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

    @admin.display(ordering="status", description="Status")
    def status_badge(self, obj):
        tone_map = {
            BookingRequest.Status.NEW: "warning",
            BookingRequest.Status.IN_REVIEW: "info",
            BookingRequest.Status.CONTACTED: "accent",
            BookingRequest.Status.CONVERTED: "success",
            BookingRequest.Status.CLOSED: "neutral",
            BookingRequest.Status.CANCELLED: "danger",
        }
        return render_admin_badge(
            obj.get_status_display(),
            tone_map.get(obj.status, "neutral"),
        )

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)

        if "status" in form.base_fields:
            form.base_fields["status"].help_text = (
                "Use this to track the request workflow. "
                "Calendar availability is blocked only after a linked Booking record is created."
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