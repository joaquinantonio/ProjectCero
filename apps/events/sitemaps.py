from django.contrib.sitemaps import Sitemap

from .models import Event


class EventSitemap(Sitemap):
    changefreq = "daily"
    priority = 0.9
    protocol = "https"

    def items(self):
        return Event.objects.filter(status=Event.Status.PUBLISHED).order_by("start_at", "title")

    def lastmod(self, obj):
        return obj.updated_at