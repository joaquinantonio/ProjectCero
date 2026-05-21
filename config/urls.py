from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.sitemaps.views import sitemap
from django.urls import include, path
from django.views.generic import TemplateView

from apps.artists.sitemaps import ArtistSitemap
from apps.events.sitemaps import EventSitemap
from apps.pages.sitemaps import StaticViewSitemap

admin.site.site_header = "CeroPJ Admin Portal"
admin.site.site_title = "CeroPJ Admin Portal"
admin.site.index_title = "Studio & Events Management Console"
admin.site.empty_value_display = "-"
# django.contrib.sitemaps.views.sitemap wired directly in urls.py,
# putting sitemap.xml at the site root lets it reference URLs across the whole site.
sitemaps = {
    "static": StaticViewSitemap,
    "artists": ArtistSitemap,
    "events": EventSitemap,
}

urlpatterns = [
    path("admin/", admin.site.urls),
    path("sitemap.xml", sitemap, {"sitemaps": sitemaps}, name="django.contrib.sitemaps.views.sitemap"),
    path("robots.txt", TemplateView.as_view(template_name="robots.txt", content_type="text/plain")),
    path("", include("apps.pages.urls")),
    path("artists/", include("apps.artists.urls")),
    path("events/", include("apps.events.urls")),
    path("studio/", include("apps.studio.urls")),
    path("bookings/", include("apps.bookings.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)