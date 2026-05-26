from django.contrib import admin, messages
from django.db.models import Count
from django.shortcuts import redirect
from django.urls import reverse
from django.utils.html import format_html
from django.utils.http import urlencode

from apps.core.admin import (
    ReadonlyOnChangeAdminMixin,
    SuperuserDeleteOnlyAdminMixin,
    TimestampedAdmin,
    make_bulk_update_action,
    render_admin_badge,
)

from .calendar_workflow import (
    create_calendar_booking_from_request,
    get_booking_initial_from_request,
    get_default_booking_resource,
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


@admin.action(description="Create confirmed calendar booking for selected requests")
def create_confirmed_bookings_from_requests(modeladmin, request, queryset):
    created = 0
    skipped = 0

    for booking_request in queryset:
        booking, message = create_calendar_booking_from_request(
            booking_request,
            status=Booking.Status.CONFIRMED,
        )

        if booking and booking_request.bookings.filter(pk=booking.pk).exists():
            # Count only newly created bookings by checking whether this request had one
            # before this action is difficult after creation; this action is still safe
            # because the helper prevents duplicates.
            if message.startswith("Calendar booking created"):
                created += 1
            else:
                skipped += 1
        else:
            skipped += 1

    if created:
        modeladmin.message_user(
            request,
            f"{created} confirmed calendar booking(s) created.",
            messages.SUCCESS,
        )

    if skipped:
        modeladmin.message_user(
            request,
            (
                f"{skipped} request(s) were skipped. "
                "They may already have bookings, be missing preferred time, or have conflicts."
            ),
            messages.WARNING,
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
        "schedule_window",
        "status_badge",
        "request",
        "created_at",
    )
    list_filter = (
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
                    "request",
                    "resource",
                ),
                "description": (
                    "Admins should normally think in terms of Booking Type: Studio or Venue. "
                    "Resource is internal and usually auto-filled to the default CeroPJ space."
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
                    "These fields control the admin calendar and public unavailable slots."
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
    actions = [
        mark_in_review,
        mark_contacted,
        mark_closed,
        create_confirmed_bookings_from_requests,
    ]
    list_select_related = ("event",)
    
    change_form_template = "admin/bookings/bookingrequest_change_form.html"

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

        if obj.status != BookingRequest.Status.CONFIRMED:
            return

        if obj.bookings.exists():
            return

        booking, message = create_calendar_booking_from_request(
            obj,
            status=Booking.Status.CONFIRMED,
        )

        if booking:
            self.message_user(
                request,
                (
                    f"Calendar booking {booking.reference_code} created for this confirmed request. "
                    "It now appears in admin calendar and public unavailable slots."
                ),
                messages.SUCCESS,
            )
        else:
            self.message_user(
                request,
                (
                    "Request is marked Confirmed, but no calendar block was created. "
                    f"{message}"
                ),
                messages.WARNING,
            )

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

    @admin.display(description="Calendar")
    def calendar_status(self, obj):
        count = getattr(obj, "bookings_total", None)
        if count is None:
            count = obj.bookings.count()

        if count:
            label = f"{count} booking" if count == 1 else f"{count} bookings"
            return render_admin_badge(label, "success")

        if obj.status == BookingRequest.Status.CONFIRMED:
            return render_admin_badge("No calendar block", "danger")

        return render_admin_badge("No booking", "neutral")

    @admin.display(description="Calendar action")
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

        url = reverse("admin:bookings_booking_add")
        params = urlencode({"request": obj.pk})
        return format_html('<a href="{}?{}">Create booking</a>', url, params)

    @admin.display(description="Calendar booking")
    def calendar_booking_link(self, obj):
        if not obj or not obj.pk:
            return "Save this request first."

        if obj.bookings.exists():
            links = []
            for booking in obj.bookings.order_by("scheduled_start_at", "id"):
                url = reverse("admin:bookings_booking_change", args=[booking.pk])
                links.append(
                    format_html(
                        '<p><a class="button" href="{}">Open {}</a> '
                        '<span class="help">{} · {} to {}</span></p>',
                        url,
                        booking.reference_code,
                        booking.get_booking_type_display(),
                        booking.scheduled_start_at.strftime("%d %b %Y, %I:%M %p"),
                        booking.scheduled_end_at.strftime("%I:%M %p"),
                    )
                )
            return format_html("{}", format_html("".join(str(link) for link in links)))

        if obj.request_type not in (
            BookingRequest.RequestType.STUDIO,
            BookingRequest.RequestType.VENUE,
        ):
            return "General enquiries do not create calendar bookings."

        url = reverse("admin:bookings_booking_add")
        params = urlencode({"request": obj.pk})
        return format_html(
            '<p><a class="button" href="{}?{}">Create calendar booking</a></p>'
            '<p class="help">This opens a prefilled Booking record. '
            'Saving that Booking is what blocks admin and public calendars.</p>',
            url,
            params,
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

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)

        if "status" in form.base_fields:
            form.base_fields["status"].help_text = (
                "Confirmed requests can automatically create a default calendar booking "
                "when preferred date and time are available."
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
