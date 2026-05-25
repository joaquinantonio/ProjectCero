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

        dashboard_cards = [
            {
                "title": "New Bookings",
                "value": BookingRequest.objects.filter(status=BookingRequest.Status.NEW).count(),
                "url": reverse("admin:bookings_bookingrequest_changelist") + "?status__exact=new",
                "hint": "Booking requests waiting for review",
            },
            {
                "title": "New Enquiries",
                "value": EnquirySubmission.objects.filter(status=EnquirySubmission.Status.NEW).count(),
                "url": reverse("admin:enquiries_enquirysubmission_changelist") + "?status__exact=new",
                "hint": "General, merch, and payment enquiries",
            },
            {
                "title": "New Artist Enquiries",
                "value": ArtistEnquiry.objects.filter(status=ArtistEnquiry.Status.NEW).count(),
                "url": reverse("admin:enquiries_artistenquiry_changelist") + "?status__exact=new",
                "hint": "Artist contact requests waiting for follow-up",
            },
            {
                "title": "Draft News",
                "value": NewsPost.objects.filter(status=NewsPost.Status.DRAFT).count(),
                "url": reverse("admin:news_newspost_changelist") + "?status__exact=draft",
                "hint": "News posts not yet published",
            },
            {
                "title": "Active Merchandise",
                "value": MerchItem.objects.filter(is_active=True).count(),
                "url": reverse("admin:merch_merchitem_changelist") + "?is_active__exact=1",
                "hint": "Catalog items currently visible",
            },
            {
                "title": "Published Events",
                "value": Event.objects.filter(status=Event.Status.PUBLISHED).count(),
                "url": reverse("admin:events_event_changelist") + "?status__exact=published",
                "hint": "Live event records",
            },
            {
                "title": "Featured Artists",
                "value": Artist.objects.filter(is_featured=True, is_active=True).count(),
                "url": reverse("admin:artists_artist_changelist") + "?is_featured__exact=1",
                "hint": "Artists shown publicly",
            },
        ]

        quick_links = [
            {"label": "Edit Website Settings", "url": site_settings_url},
            {"label": "Admin Calendar", "url": reverse("admin:schedule_calendar")},
            {"label": "Review Booking Requests", "url": reverse("admin:bookings_bookingrequest_changelist")},
            {"label": "Review Enquiries", "url": reverse("admin:enquiries_enquirysubmission_changelist")},
            {"label": "Review Artist Enquiries", "url": reverse("admin:enquiries_artistenquiry_changelist") + "?status__exact=new"},
            {"label": "Add New Event", "url": reverse("admin:events_event_add")},
            {"label": "Add News Post", "url": reverse("admin:news_newspost_add")},
            {"label": "Add Merch Item", "url": reverse("admin:merch_merchitem_add")},
        ]

        dashboard_sections = [
            {
                "title": "Website",
                "items": [
                    {
                        "label": "Website Settings",
                        "url": site_settings_url,
                        "hint": "Brand, contact details, social links",
                    },
                    {
                        "label": "Page Sections",
                        "url": reverse("admin:pages_pagesection_changelist"),
                        "hint": "Homepage, about, and contact content blocks",
                    },
                ],
            },
            {
                "title": "Bookings",
                "items": [
                    {
                        "label": "Booking Requests",
                        "url": reverse("admin:bookings_bookingrequest_changelist"),
                        "hint": "Review and update booking requests",
                    },
                    {
                        "label": "Calendar",
                        "url": reverse("admin:schedule_calendar"),
                        "hint": "View events, studio service bookings, and venue / private event bookings by time",
                    },
                ],
            },
            {
                "title": "Enquiries",
                "items": [
                    {
                        "label": "Enquiries",
                        "url": reverse("admin:enquiries_enquirysubmission_changelist"),
                        "hint": "Review general, merch, and payment enquiries",
                    },
                    {
                        "label": "Artist Enquiries",
                        "url": reverse("admin:enquiries_artistenquiry_changelist"),
                        "hint": "Review artist contact requests and call/WhatsApp users",
                    },
                ],
            },
            {
                "title": "News",
                "items": [
                    {
                        "label": "Articles",
                        "url": reverse("admin:news_newspost_changelist"),
                        "hint": "Manage public updates and announcements",
                    },
                ],
            },
            {
                "title": "Events & Artists",
                "items": [
                    {
                        "label": "Events",
                        "url": reverse("admin:events_event_changelist"),
                        "hint": "Create and publish event listings",
                    },
                    {
                        "label": "Event Categories",
                        "url": reverse("admin:events_eventcategory_changelist"),
                        "hint": "Manage event grouping options",
                    },
                    {
                        "label": "Artists",
                        "url": reverse("admin:artists_artist_changelist"),
                        "hint": "Manage featured artist profiles",
                    },
                ],
            },
            {
                "title": "Studio",
                "items": [
                    {
                        "label": "Studio Services",
                        "url": reverse("admin:studio_studioservice_changelist"),
                        "hint": "Manage studio offerings, pricing, duration, images, and display order",
                    },
                ],
            },
            {
                "title": "Merchandise",
                "items": [
                    {
                        "label": "Merchandise",
                        "url": reverse("admin:merch_merchitem_changelist"),
                        "hint": "Manage the merchandise catalog",
                    },
                ],
            }
        ]

        if request.user.is_superuser:
            dashboard_sections.append(
                {
                    "title": "Admin & Permissions",
                    "items": [
                        {
                            "label": "Users",
                            "url": reverse("admin:auth_user_changelist"),
                            "hint": "Manage admin users",
                        },
                        {
                            "label": "Groups",
                            "url": reverse("admin:auth_group_changelist"),
                            "hint": "Manage roles and permissions",
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