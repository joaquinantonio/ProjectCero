from django.contrib.sitemaps import Sitemap

from .models import Artist


class ArtistSitemap(Sitemap):
    changefreq = "weekly"
    priority = 0.7
    protocol = "https"

    def items(self):
        return Artist.objects.filter(is_active=True, is_featured=True).order_by("feature_order", "name")

    def lastmod(self, obj):
        return obj.updated_at