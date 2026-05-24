from django.db.models import Q
from django.http import Http404
from django.shortcuts import render

from apps.core.utils import paginate_queryset
from apps.events.selectors import (
    get_past_events_for_artist,
    get_upcoming_events_for_artist,
)

from .models import Artist
from .selectors import get_artist_by_slug, get_featured_artists


def artist_list_view(request):
    featured_artists = get_featured_artists()
    search_query = request.GET.get("q", "").strip()

    if search_query:
        featured_artists = featured_artists.filter(
            Q(name__icontains=search_query)
            | Q(short_bio__icontains=search_query)
            | Q(bio__icontains=search_query)
        )

    page_obj = paginate_queryset(request, featured_artists, per_page=8)

    return render(
        request,
        "artists/artist_list.html",
        {
            "featured_artists": page_obj,
            "search_query": search_query,
        },
    )


def artist_detail_view(request, slug):
    try:
        artist = get_artist_by_slug(slug)
    except Artist.DoesNotExist:
        raise Http404("Artist not found")

    upcoming_events = get_upcoming_events_for_artist(artist, limit=6)
    past_events = get_past_events_for_artist(artist, limit=6)

    return render(
        request,
        "artists/artist_detail.html",
        {
            "artist": artist,
            "upcoming_events": upcoming_events,
            "past_events": past_events,
        },
    )