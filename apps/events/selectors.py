from django.db.models import Prefetch, Q
from django.utils import timezone

from apps.artists.models import Artist
from apps.artists.selectors import get_artist_by_slug, get_featured_artists
from apps.core.utils import apply_limit
from .models import Event, EventArtist


def base_public_events_queryset():
    return (
        Event.objects.filter(status=Event.Status.PUBLISHED)
        .select_related("category")
        .prefetch_related(
            Prefetch(
                "event_artists",
                queryset=EventArtist.objects.select_related("artist").order_by("sort_order", "id"),
            )
        )
    )


def get_upcoming_events(limit=None, featured_only=False):
    now = timezone.now()

    qs = base_public_events_queryset().filter(
        Q(start_at__gte=now) |
        Q(end_at__isnull=False, end_at__gte=now)
    )

    if featured_only:
        qs = qs.filter(is_featured=True)

    qs = qs.order_by("start_at", "title")

    if limit:
        return qs[:limit]
    return qs


def get_past_events(limit=None):
    now = timezone.now()

    qs = base_public_events_queryset().filter(
        Q(end_at__lt=now) |
        Q(end_at__isnull=True, start_at__lt=now)
    ).order_by("-start_at", "-id")

    if limit:
        return qs[:limit]
    return qs


def get_published_event_by_slug(slug):
    return base_public_events_queryset().get(slug=slug)


def get_related_upcoming_events(event, limit=3):
    now = timezone.now()

    qs = (
        base_public_events_queryset()
        .filter(start_at__gte=now)
        .exclude(id=event.id)
    )

    if event.category_id:
        qs = qs.filter(category_id=event.category_id)

    return qs.order_by("start_at", "title")[:limit]


def get_calendar_events_between(start_dt=None, end_dt=None):
    qs = base_public_events_queryset()

    if start_dt and end_dt:
        qs = qs.filter(
            Q(start_at__lt=end_dt) &
            (
                Q(end_at__isnull=True, start_at__gte=start_dt) |
                Q(end_at__isnull=False, end_at__gte=start_dt)
            )
        )

    return qs.order_by("start_at", "title")


def get_housebands(limit=None):
    # No dedicated 'is_houseband' field exists on Artist; fall back to featured artists.
    qs = get_featured_artists()
    return apply_limit(qs, limit)


def get_non_houseband_featured_artists(limit=None):
    # Return featured artists (same as get_featured_artists) for now. If a dedicated
    # is_houseband field is added later, this function can be updated.
    qs = get_featured_artists()
    return apply_limit(qs, limit)


# get_artist_by_slug is provided by apps.artists.selectors; import that


def get_upcoming_events_for_artist(artist, limit=None):
    now = timezone.now()

    qs = (
        base_public_events_queryset()
        .filter(
            event_artists__artist=artist
        )
        .filter(
            Q(start_at__gte=now) |
            Q(end_at__isnull=False, end_at__gte=now)
        )
        .distinct()
        .order_by("start_at", "title")
    )

    if limit:
        return qs[:limit]
    return qs


def get_past_events_for_artist(artist, limit=None):
    now = timezone.now()

    qs = (
        base_public_events_queryset()
        .filter(event_artists__artist=artist)
        .filter(
            Q(end_at__lt=now) |
            Q(end_at__isnull=True, start_at__lt=now)
        )
        .distinct()
        .order_by("-start_at", "-id")
    )

    if limit:
        return qs[:limit]
    return qs