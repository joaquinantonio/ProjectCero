from django.contrib import admin
from django.db.models import Count
from django.shortcuts import redirect
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
    mark_bookings_cancelled,
    mark_bookings_completed,
    mark_bookings_confirmed,
    mark_bookings_no_show,
    mark_bookings_tentative,
    mark_cancelled,
    mark_closed,
    mark_contacted,
    mark_in_review,
)
from .admin_filters import (
    BookingRequestCalendarStatusFilter,
    BookingScheduleFilter,
)
from .calendar_workflow import (
    get_booking_initial_from_request,
    get_default_booking_resource,
)
from .models import Booking, BookingRequest, BookingResource, ScheduleCalendar


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
        "schedule_window",
        "status_badge",
        "calendar_effect_badge",
        "request_link",
        "created_at",
    )
    list_filter = (
        BookingScheduleFilter,
        "booking_type",
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
        "email, phone, or notes."
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
    actions = [
        mark_bookings_tentative,
        mark_bookings_confirmed,
        mark_bookings_cancelled,
        mark_bookings_completed,
        mark_bookings_no_show,
    ]

    readonly_fields = (
        "reference_code",
        "calendar_effect_badge",
        "request_summary",
        "created_at",
        "updated_at",
    )

    def get_fieldsets(self, request, obj=None):
        return (
            (
                "Booking Status",
                {
                    "fields": (
                        "reference_code",
                        "booking_type",
                        "status",
                        "calendar_effect_badge",
                        "title",
                    ),
                    "description": (
                        "Use Booking Type and Status to manage the operational booking. "
                        "Tentative and Confirmed bookings block the public availability calendar."
                    ),
                },
            ),
            (
                "Linked Public Request",
                {
                    "fields": (
                        "request",
                        "request_summary",
                    ),
                    "description": (
                        "Optional, but recommended. Linking a public request helps staff trace "
                        "who submitted the original booking enquiry."
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
                        "These are the actual calendar times. They control the admin calendar "
                        "and public unavailable slots."
                    ),
                },
            ),
            (
                "Internal Resource",
                {
                    "fields": ("resource",),
                    "classes": ("collapse",),
                    "description": (
                        "Internal resource used for conflict checking. For now this should usually "
                        "be the default CeroPJ Venue resource."
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

    def get_changeform_initial_data(self, request):
        initial = super().get_changeform_initial_data(request)

        request_id = request.GET.get("request")
        if not request_id:
            return initial

        try:
            booking_request = BookingRequest.objects.get(pk=request_id)
        except BookingRequest.DoesNotExist:
            return initial

        initial.update(get_booking_initial_from_request(booking_request))
        return initial

    def save_model(self, request, obj, form, change):
        if not obj.resource_id:
            default_resource = get_default_booking_resource()
            if default_resource:
                obj.resource = default_resource

        super().save_model(request, obj, form, change)

        if obj.request_id and obj.request.status != BookingRequest.Status.CONVERTED:
            obj.request.status = BookingRequest.Status.CONVERTED
            obj.request.save(update_fields=["status", "updated_at"])

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
        start_at = timezone.localtime(obj.scheduled_start_at)
        end_at = timezone.localtime(obj.scheduled_end_at)

        return f"{start_at:%d %b %Y, %I:%M %p} – {end_at:%I:%M %p}"

    @admin.display(description="Calendar effect")
    def calendar_effect_badge(self, obj):
        if not obj:
            return "-"

        if obj.status in Booking.BLOCKING_STATUSES:
            return render_admin_badge("Blocks availability", "success")

        return render_admin_badge("Does not block", "neutral")

    @admin.display(description="Request")
    def request_link(self, obj):
        if not obj.request_id:
            return "-"

        url = reverse("admin:bookings_bookingrequest_change", args=[obj.request_id])
        return format_html(
            '<a href="{}">{}</a>',
            url,
            obj.request.reference_code,
        )

    @admin.display(description="Request summary")
    def request_summary(self, obj):
        if not obj or not obj.request_id:
            return "No public request is linked to this booking."

        booking_request = obj.request
        request_url = reverse(
            "admin:bookings_bookingrequest_change",
            args=[booking_request.pk],
        )

        preferred_time = "-"

        if booking_request.preferred_start_time and booking_request.preferred_end_time:
            preferred_time = (
                f"{booking_request.preferred_start_time:%I:%M %p} – "
                f"{booking_request.preferred_end_time:%I:%M %p}"
            )
        elif booking_request.preferred_start_time:
            preferred_time = f"{booking_request.preferred_start_time:%I:%M %p}"

        rows = (
            ("Reference", booking_request.reference_code),
            ("Type", booking_request.get_request_type_display()),
            ("Customer", booking_request.name),
            ("Email", booking_request.email),
            ("Phone", booking_request.phone or "-"),
            ("Preferred date", booking_request.preferred_date or "-"),
            ("Preferred time", preferred_time),
            ("Guest count", booking_request.guest_count or "-"),
        )

        return format_html(
            '<div class="cero-admin-summary">'
            '<p><a class="button" href="{}">Open original request</a></p>'
            '<dl>{}</dl>'
            '</div>',
            request_url,
            format_html_join(
                "",
                "<dt><strong>{}</strong></dt><dd>{}</dd>",
                rows,
            ),
        )

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)

        if "status" in form.base_fields:
            form.base_fields["status"].help_text = (
                "Tentative and Confirmed bookings block availability. "
                "Cancelled, Completed, and No Show bookings do not block availability."
            )

        if "title" in form.base_fields:
            form.base_fields["title"].help_text = (
                "Optional internal title. If left blank, the linked request name is used."
            )

        if "scheduled_start_at" in form.base_fields:
            form.base_fields["scheduled_start_at"].help_text = (
                "Actual booking start time shown on admin and public availability calendars."
            )

        if "scheduled_end_at" in form.base_fields:
            form.base_fields["scheduled_end_at"].help_text = (
                "Actual booking end time. Must be after the start time."
            )

        if "internal_notes" in form.base_fields:
            form.base_fields["internal_notes"].widget.attrs["rows"] = 8
            form.base_fields["internal_notes"].help_text = "Visible only in admin."

        if "request" in form.base_fields:
            form.base_fields["request"].help_text = (
                "Optional. Link this booking to the original public request."
            )

        if "resource" in form.base_fields:
            default_resource = get_default_booking_resource()
            if default_resource:
                form.base_fields["resource"].initial = default_resource.pk

            form.base_fields["resource"].label = "Internal resource"
            form.base_fields["resource"].help_text = (
                "Usually auto-filled to the default CeroPJ space. "
                "Admins normally only need to choose Studio or Venue as the booking type."
            )

        if "booking_type" in form.base_fields:
            form.base_fields["booking_type"].help_text = (
                "This is what admins should use operationally: Studio or Venue."
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