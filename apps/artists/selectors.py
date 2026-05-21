from .models import Artist


def get_featured_artists(limit=None):
    qs = Artist.objects.featured().order_by("feature_order", "name")
    from apps.core.utils import apply_limit

    return apply_limit(qs, limit)


def get_artist_by_slug(slug):
    return Artist.objects.get(
        slug=slug,
        is_active=True,
    )