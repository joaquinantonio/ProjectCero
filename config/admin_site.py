from django.contrib.admin import AdminSite
from django.core.exceptions import PermissionDenied
from apps.artists.models import Artist
from apps.bookings.availability import get_confirmed_booking_blocks, get_event_blocks
from apps.bookings.models import Booking, BookingRequest
from apps.enquiries.models import EnquirySubmission, ArtistEnquiry
from apps.events.models import Event
from apps.merch.models import MerchItem
from apps.news.models import NewsPost
from apps.pages.selectors import get_site_settings
from django.http import JsonResponse
from django.template.response import TemplateResponse
from django.urls import path, reverse
from django.utils.dateparse import parse_datetime


class CeroAdminSite(AdminSite):
    site_header = "CeroPJ Control Room"
    site_title = "CeroPJ Control Room"
    index_title = "Admin Dashboard"
    empty_value_display = "-"
    index_template = "admin/custom_index.html"
    # enable_nav_sidebar = False
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
            site_settings_url = reverse("admin:pages_sitesettings_change", args=[site_settings.pk])
        else:
            site_settings_url = reverse("admin:pages_sitesettings_add")

        # Booking workflow focused metrics
        dashboard_cards = [
            {
                "title": "🔴 New Bookings",
                "value": BookingRequest.objects.filter(status=BookingRequest.Status.NEW).count(),
                "url": reverse("admin:bookings_bookingrequest_changelist") + "?status__exact=new",
                "hint": "Awaiting your initial review",
            },
            {
                "title": "🟡 In Review",
                "value": BookingRequest.objects.filter(status=BookingRequest.Status.IN_REVIEW).count(),
                "url": reverse("admin:bookings_bookingrequest_changelist") + "?status__exact=in_review",
                "hint": "You're actively reviewing these",
            },
            {
                "title": "🟠 Contacted",
                "value": BookingRequest.objects.filter(status=BookingRequest.Status.CONTACTED).count(),
                "url": reverse("admin:bookings_bookingrequest_changelist") + "?status__exact=contacted",
                "hint": "Waiting for customer response",
            },
            {
                "title": "✓ Confirmed",
                "value": BookingRequest.objects.filter(status=BookingRequest.Status.CONFIRMED).count(),
                "url": reverse("admin:bookings_bookingrequest_changelist") + "?status__exact=confirmed",
                "hint": "Calendar bookings created",
            },
        ]

        # Highlight primary action prominently if new bookings exist
        new_booking_count = BookingRequest.objects.filter(status=BookingRequest.Status.NEW).count()

        # Quick actions - primary focus on "Review New Bookings" when urgent
        quick_links = []
        if new_booking_count > 0:
            quick_links.append({
                "label": f"🔴 Review {new_booking_count} New Booking{'s' if new_booking_count != 1 else ''}",
                "url": reverse("admin:bookings_bookingrequest_changelist") + "?status__exact=new",
                "is_primary": True,
            })

        quick_links.extend([
            {"label": "📅 Calendar", "url": reverse("admin:schedule_calendar"), "is_primary": False},
            {"label": "🟡 In Review", "url": reverse("admin:bookings_bookingrequest_changelist") + "?status__exact=in_review", "is_primary": False},
            {"label": "🟠 Follow Up", "url": reverse("admin:bookings_bookingrequest_changelist") + "?status__exact=contacted", "is_primary": False},
        ])

        # Consolidated dashboard sections (2-3 primary categories)
        dashboard_sections = [
            {
                "title": "📅 Booking Workflow",
                "items": [
                    {
                        "label": "Booking Requests",
                        "url": reverse("admin:bookings_bookingrequest_changelist"),
                        "hint": "Manage all booking requests through workflow stages",
                    },
                    {
                        "label": "Calendar",
                        "url": reverse("admin:schedule_calendar"),
                        "hint": "View blocked time, events, and confirmed bookings",
                    },
                    {
                        "label": "Calendar Bookings",
                        "url": reverse("admin:bookings_booking_changelist"),
                        "hint": "Manage created bookings and blocks",
                    },
                ],
            },
            {
                "title": "📋 Support & Content",
                "items": [
                    {
                        "label": "General Inquiries",
                        "url": reverse("admin:enquiries_enquirysubmission_changelist"),
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
        extra_context["can_view_schedule"] = True
        extra_context["schedule_calendar_url"] = reverse("admin:schedule_calendar")

        return super().index(request, extra_context=extra_context)