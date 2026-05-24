from apps.core.utils import apply_limit

from .models import Artist


def get_featured_artists(limit=None):
    queryset = Artist.objects.featured().order_by("feature_order", "name")
    return apply_limit(queryset, limit)


def get_artist_by_slug(slug):
    return Artist.objects.get(
        slug=slug,
        is_active=True,
    )