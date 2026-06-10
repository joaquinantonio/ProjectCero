from datetime import timedelta

from django.contrib.admin import AdminSite
from django.core.exceptions import PermissionDenied
from django.db.models import Count, Q
from django.http import JsonResponse
from django.template.response import TemplateResponse
from django.urls import path, reverse
from django.utils import timezone
from django.utils.dateparse import parse_datetime

from apps.bookings.availability import get_confirmed_booking_blocks, get_event_blocks
from apps.bookings.models import Booking, BookingRequest
from apps.pages.selectors import get_site_settings


class CeroAdminSite(AdminSite):
    site_header = "CeroPJ Admin Site"
    site_title = "CeroPJ Admin Site"
    index_title = "Admin Dashboard"
    empty_value_display = "-"
    index_template = "admin/custom_index.html"

    def has_schedule_permission(self, request):
        return (
            request.user.is_superuser
            or request.user.has_perm("bookings.view_bookingrequest")
            or request.user.has_perm("bookings.view_booking")
            or request.user.has_perm("events.view_event")
        )

    def get_urls(self):
        custom_urls = [
            path(
                "schedule/",
                self.admin_view(self.schedule_calendar_view),
                name="schedule_calendar",
            ),
            path(
                "schedule/feed/",
                self.admin_view(self.schedule_calendar_feed_view),
                name="schedule_calendar_feed",
            ),
        ]
        return custom_urls + super().get_urls()

    def schedule_calendar_view(self, request):
        if not self.has_schedule_permission(request):
            raise PermissionDenied

        context = dict(self.each_context(request))
        context.update(
            {
                "title": "Admin Calendar",
                "business_hours_text": "11:00 AM – 12:00 midnight",
            }
        )
        return TemplateResponse(request, "admin/admin_calendar.html", context)

    def schedule_calendar_feed_view(self, request):
        if not self.has_schedule_permission(request):
            raise PermissionDenied

        start_raw = request.GET.get("start")
        end_raw = request.GET.get("end")

        start_dt = parse_datetime(start_raw) if start_raw else None
        end_dt = parse_datetime(end_raw) if end_raw else None

        calendar_items = []

        for block in get_event_blocks(start_dt=start_dt, end_dt=end_dt):
            event = block["object"]

            calendar_items.append(
                {
                    "title": f"Event: {event.title}",
                    "start": block["start"].isoformat(),
                    "end": block["end"].isoformat(),
                    "url": reverse("admin:events_event_change", args=[event.pk]),
                    "classNames": ["schedule-event", "schedule-event-main"],
                }
            )

        booking_label_map = {
            Booking.BookingType.STUDIO: "Studio",
            Booking.BookingType.VENUE: "Venue",
        }

        booking_class_map = {
            Booking.BookingType.STUDIO: "schedule-event-studio",
            Booking.BookingType.VENUE: "schedule-event-venue",
        }

        for block in get_confirmed_booking_blocks(start_dt=start_dt, end_dt=end_dt):
            booking = block["object"]

            type_label = booking_label_map.get(
                booking.booking_type,
                booking.get_booking_type_display(),
            )

            css_class = booking_class_map.get(
                booking.booking_type,
                "schedule-event-booking",
            )

            calendar_items.append(
                {
                    "title": f"{type_label}: {booking.display_title}",
                    "start": block["start"].isoformat(),
                    "end": block["end"].isoformat(),
                    "url": reverse("admin:bookings_booking_change", args=[booking.pk]),
                    "classNames": ["schedule-event", css_class],
                }
            )

        return JsonResponse(calendar_items, safe=False)

    def index(self, request, extra_context=None):
        extra_context = extra_context or {}

        site_settings = get_site_settings()
        if site_settings:
            site_settings_url = reverse(
                "admin:pages_sitesettings_change",
                args=[site_settings.pk],
            )
        else:
            site_settings_url = reverse("admin:pages_sitesettings_add")

        booking_request_changelist_url = reverse(
            "admin:bookings_bookingrequest_changelist"
        )
        booking_changelist_url = reverse("admin:bookings_booking_changelist")
        schedule_calendar_url = reverse("admin:schedule_calendar")

        now = timezone.now()
        week_end = now + timedelta(days=7)

        request_counts = BookingRequest.objects.aggregate(
            new_count=Count(
                "id",
                filter=Q(status=BookingRequest.Status.NEW),
            ),
            in_review_count=Count(
                "id",
                filter=Q(status=BookingRequest.Status.IN_REVIEW),
            ),
            contacted_count=Count(
                "id",
                filter=Q(status=BookingRequest.Status.CONTACTED),
            ),
            converted_count=Count(
                "id",
                filter=Q(status=BookingRequest.Status.CONVERTED),
            ),
            needs_calendar_count=Count(
                "id",
                filter=Q(
                    request_type__in=[
                        BookingRequest.RequestType.STUDIO,
                        BookingRequest.RequestType.VENUE,
                    ],
                    bookings__isnull=True,
                    preferred_date__isnull=False,
                    preferred_start_time__isnull=False,
                    preferred_end_time__isnull=False,
                ),
            ),
            missing_time_count=Count(
                "id",
                filter=(
                    Q(
                        request_type__in=[
                            BookingRequest.RequestType.STUDIO,
                            BookingRequest.RequestType.VENUE,
                        ],
                        bookings__isnull=True,
                    )
                    & (
                        Q(preferred_date__isnull=True)
                        | Q(preferred_start_time__isnull=True)
                        | Q(preferred_end_time__isnull=True)
                    )
                ),
            ),
        )

        upcoming_booking_count = Booking.objects.filter(
            scheduled_end_at__gte=now,
        ).count()

        this_week_booking_count = Booking.objects.filter(
            scheduled_start_at__gte=now,
            scheduled_start_at__lt=week_end,
        ).count()

        blocking_booking_count = Booking.objects.filter(
            status__in=Booking.BLOCKING_STATUSES,
        ).count()

        dashboard_cards = [
            {
                "title": "🔴 New Requests",
                "value": request_counts["new_count"],
                "url": booking_request_changelist_url + "?status__exact=new",
                "hint": "New booking requests awaiting initial review",
            },
            {
                "title": "🧩 Need Calendar Booking",
                "value": request_counts["needs_calendar_count"],
                "url": booking_request_changelist_url
                + "?calendar_status=needs_booking",
                "hint": "Requests with date/time ready but no calendar booking yet",
            },
            {
                "title": "📅 Upcoming Bookings",
                "value": upcoming_booking_count,
                "url": booking_changelist_url + "?schedule_timing=upcoming",
                "hint": "Future bookings already created in the calendar",
            },
            {
                "title": "🚧 Blocking Availability",
                "value": blocking_booking_count,
                "url": booking_changelist_url + "?schedule_timing=blocking",
                "hint": "Tentative and confirmed bookings blocking public availability",
            },
        ]

        quick_links = []

        if request_counts["new_count"] > 0:
            quick_links.append(
                {
                    "label": (
                        f"🔴 Review {request_counts['new_count']} "
                        f"New Request{'s' if request_counts['new_count'] != 1 else ''}"
                    ),
                    "url": booking_request_changelist_url + "?status__exact=new",
                    "is_primary": True,
                }
            )

        if request_counts["needs_calendar_count"] > 0:
            quick_links.append(
                {
                    "label": (
                        f"🧩 Create {request_counts['needs_calendar_count']} "
                        f"Calendar Booking"
                        f"{'s' if request_counts['needs_calendar_count'] != 1 else ''}"
                    ),
                    "url": booking_request_changelist_url
                    + "?calendar_status=needs_booking",
                    "is_primary": True,
                }
            )

        quick_links.extend(
            [
                {
                    "label": "📅 Admin Calendar",
                    "url": schedule_calendar_url,
                    "is_primary": False,
                },
                {
                    "label": "📌 Upcoming Bookings",
                    "url": booking_changelist_url + "?schedule_timing=upcoming",
                    "is_primary": False,
                },
                {
                    "label": "⚠️ Missing Date/Time",
                    "url": booking_request_changelist_url
                    + "?calendar_status=missing_time",
                    "is_primary": False,
                },
                {
                    "label": "🟡 In Review",
                    "url": booking_request_changelist_url
                    + "?status__exact=in_review",
                    "is_primary": False,
                },
                {
                    "label": "🟠 Follow Up",
                    "url": booking_request_changelist_url
                    + "?status__exact=contacted",
                    "is_primary": False,
                },
            ]
        )

        dashboard_sections = [
            {
                "title": "📅 Booking Operations",
                "items": [
                    {
                        "label": "Requests Needing Calendar Booking",
                        "url": booking_request_changelist_url
                        + "?calendar_status=needs_booking",
                        "hint": "Requests with complete preferred date/time but no linked booking",
                    },
                    {
                        "label": "Missing Preferred Date/Time",
                        "url": booking_request_changelist_url
                        + "?calendar_status=missing_time",
                        "hint": "Requests that cannot become calendar bookings yet",
                    },
                    {
                        "label": "Converted Requests",
                        "url": booking_request_changelist_url
                        + "?status__exact=converted",
                        "hint": "Requests already converted into calendar bookings",
                    },
                    {
                        "label": "Upcoming Calendar Bookings",
                        "url": booking_changelist_url + "?schedule_timing=upcoming",
                        "hint": "Future booking records that staff need to manage",
                    },
                    {
                        "label": "Admin Calendar",
                        "url": schedule_calendar_url,
                        "hint": "Visual calendar of events, studio bookings, and venue bookings",
                    },
                ],
            },
            {
                "title": "📋 Booking Workflow",
                "items": [
                    {
                        "label": "All Booking Requests",
                        "url": booking_request_changelist_url,
                        "hint": "Review customer booking requests and workflow status",
                    },
                    {
                        "label": "All Calendar Bookings",
                        "url": booking_changelist_url,
                        "hint": "Manage actual booking records that block availability",
                    },
                    {
                        "label": "This Week's Bookings",
                        "url": booking_changelist_url + "?schedule_timing=this_week",
                        "hint": (
                            f"{this_week_booking_count} booking"
                            f"{'s' if this_week_booking_count != 1 else ''} "
                            "scheduled in the next 7 days"
                        ),
                    },
                    {
                        "label": "Blocking Availability",
                        "url": booking_changelist_url + "?schedule_timing=blocking",
                        "hint": "Tentative and confirmed bookings currently blocking availability",
                    },
                ],
            },
            {
                "title": "📋 Support & Content",
                "items": [
                    {
                        "label": "General Inquiries",
                        "url": reverse(
                            "admin:enquiries_enquirysubmission_changelist"
                        ),
                        "hint": "Merch, payment, and general enquiries",
                    },
                    {
                        "label": "Artist Inquiries",
                        "url": reverse("admin:enquiries_artistenquiry_changelist"),
                        "hint": "Artist collaboration requests",
                    },
                    {
                        "label": "Events",
                        "url": reverse("admin:events_event_changelist"),
                        "hint": "Event listings",
                    },
                    {
                        "label": "News",
                        "url": reverse("admin:news_newspost_changelist"),
                        "hint": "Updates and announcements",
                    },
                ],
            },
            {
                "title": "⚙️ Settings",
                "items": [
                    {
                        "label": "Website",
                        "url": site_settings_url,
                        "hint": "Brand, contact, social links",
                    },
                    {
                        "label": "Studio Services",
                        "url": reverse("admin:studio_studioservice_changelist"),
                        "hint": "Services and pricing",
                    },
                    {
                        "label": "Merchandise",
                        "url": reverse("admin:merch_merchitem_changelist"),
                        "hint": "Merch catalog",
                    },
                ],
            },
        ]

        if request.user.is_superuser:
            dashboard_sections.append(
                {
                    "title": "🔐 Admin",
                    "items": [
                        {
                            "label": "Users",
                            "url": reverse("admin:auth_user_changelist"),
                            "hint": "Admin users",
                        },
                        {
                            "label": "Permissions",
                            "url": reverse("admin:auth_group_changelist"),
                            "hint": "Roles and permissions",
                        },
                    ],
                }
            )

        extra_context["dashboard_cards"] = dashboard_cards
        extra_context["quick_links"] = quick_links
        extra_context["dashboard_sections"] = dashboard_sections
        extra_context["can_view_schedule"] = self.has_schedule_permission(request)
        extra_context["schedule_calendar_url"] = schedule_calendar_url

        return super().index(request, extra_context=extra_context)