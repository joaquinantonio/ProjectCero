from django.db.models import Prefetch, Q
from django.utils import timezone

from apps.core.utils import apply_limit

from .models import Event, EventArtist


def base_public_events_queryset():
    return (
        Event.objects.filter(status=Event.Status.PUBLISHED)
        .select_related("category")
        .prefetch_related(
            Prefetch(
                "event_artists",
                queryset=EventArtist.objects.select_related("artist").order_by(
                    "sort_order",
                    "id",
                ),
            )
        )
    )


def get_upcoming_events(limit=None, featured_only=False):
    now = timezone.now()

    queryset = base_public_events_queryset().filter(
        Q(start_at__gte=now)
        | Q(end_at__isnull=False, end_at__gte=now)
    )

    if featured_only:
        queryset = queryset.filter(is_featured=True)

    queryset = queryset.order_by("start_at", "title")
    return apply_limit(queryset, limit)


def get_past_events(limit=None):
    now = timezone.now()

    queryset = (
        base_public_events_queryset()
        .filter(
            Q(end_at__lt=now)
            | Q(end_at__isnull=True, start_at__lt=now)
        )
        .order_by("-start_at", "-id")
    )

    return apply_limit(queryset, limit)


def get_published_event_by_slug(slug):
    return base_public_events_queryset().get(slug=slug)


def get_related_upcoming_events(event, limit=3):
    now = timezone.now()

    queryset = (
        base_public_events_queryset()
        .filter(start_at__gte=now)
        .exclude(id=event.id)
    )

    if event.category_id:
        queryset = queryset.filter(category_id=event.category_id)

    queryset = queryset.order_by("start_at", "title")
    return apply_limit(queryset, limit)


def get_calendar_events_between(start_dt=None, end_dt=None):
    queryset = base_public_events_queryset()

    if start_dt and end_dt:
        queryset = queryset.filter(
            Q(start_at__lt=end_dt)
            & (
                Q(end_at__isnull=True, start_at__gte=start_dt)
                | Q(end_at__isnull=False, end_at__gte=start_dt)
            )
        )

    return queryset.order_by("start_at", "title")


def get_upcoming_events_for_artist(artist, limit=None):
    now = timezone.now()

    queryset = (
        base_public_events_queryset()
        .filter(event_artists__artist=artist)
        .filter(
            Q(start_at__gte=now)
            | Q(end_at__isnull=False, end_at__gte=now)
        )
        .distinct()
        .order_by("start_at", "title")
    )

    return apply_limit(queryset, limit)


def get_past_events_for_artist(artist, limit=None):
    now = timezone.now()

    queryset = (
        base_public_events_queryset()
        .filter(event_artists__artist=artist)
        .filter(
            Q(end_at__lt=now)
            | Q(end_at__isnull=True, start_at__lt=now)
        )
        .distinct()
        .order_by("-start_at", "-id")
    )

    return apply_limit(queryset, limit)