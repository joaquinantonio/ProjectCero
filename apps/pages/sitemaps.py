from django.contrib.sitemaps import Sitemap
from django.urls import reverse


class StaticViewSitemap(Sitemap):
    priority = 0.8
    changefreq = "weekly"
    protocol = "https"

    def items(self):
        return [
            "pages:home",
            "pages:about",
            "pages:contact",
            "studio:home",
            "artists:artist_list",
            "events:event_list",
            "events:past_event_list",
            "events:calendar",
            "bookings:landing",
        ]

    def location(self, item):
        return reverse(item)