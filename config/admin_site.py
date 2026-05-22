from django.contrib.admin import AdminSite
from django.urls import reverse

from apps.artists.models import Artist
from apps.bookings.models import BookingRequest
from apps.events.models import Event
from apps.pages.selectors import get_site_settings
from apps.studio.models import StudioService


class CeroAdminSite(AdminSite):
    site_header = "CeroPJ Admin"
    site_title = "CeroPJ Admin"
    index_title = "Site Control Panel"
    empty_value_display = "-"
    index_template = "admin/custom_index.html"
    # enable_nav_sidebar = False

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
                "hint": "Requests waiting for review",
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
            {
                "title": "Active Services",
                "value": StudioService.objects.filter(is_active=True).count(),
                "url": reverse("admin:studio_studioservice_changelist") + "?is_active__exact=1",
                "hint": "Studio services currently visible",
            },
        ]

        quick_links = [
            {"label": "Edit Website Settings", "url": site_settings_url},
            {"label": "Review Booking Requests", "url": reverse("admin:bookings_bookingrequest_changelist")},
            {"label": "Add New Event", "url": reverse("admin:events_event_add")},
            {"label": "Add New Artist", "url": reverse("admin:artists_artist_add")},
            {"label": "Add Studio Service", "url": reverse("admin:studio_studioservice_add")},
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
                        "hint": "Review and update enquiries",
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
                        "hint": "Manage studio offerings and display order",
                    },
                    {
                        "label": "Studio Categories",
                        "url": reverse("admin:studio_studioservicecategory_changelist"),
                        "hint": "Manage service categories",
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

        return super().index(request, extra_context=extra_context)