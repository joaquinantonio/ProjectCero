from django.shortcuts import render

from apps.artists.selectors import get_featured_artists
from apps.events.selectors import get_upcoming_events
from apps.merch.models import MerchItem
from apps.news.models import NewsPost
from apps.studio.models import StudioService

from .models import PageSection


def get_page_sections(page_key):
    return (
        PageSection.objects.for_page_active(page_key)
        .order_by("sort_order", "id")
    )


def home_view(request):
    upcoming_events = get_upcoming_events(limit=6)

    featured_services = (
        StudioService.objects.featured()
        .select_related("category")
        .order_by("display_order", "name")[:4]
    )

    featured_artists = get_featured_artists(limit=4)

    latest_news = (
        NewsPost.objects.filter(status=NewsPost.Status.PUBLISHED)
        .order_by("-published_at", "-created_at")[:3]
    )

    featured_merch = (
        MerchItem.objects.filter(is_active=True, is_featured=True)
        .order_by("display_order", "name")[:4]
    )

    context = {
        "sections": get_page_sections("home"),
        "upcoming_events": upcoming_events,
        "featured_services": featured_services,
        "featured_artists": featured_artists,
        "latest_news": latest_news,
        "featured_merch": featured_merch,
    }
    return render(request, "pages/home.html", context)


def about_view(request):
    context = {
        "sections": get_page_sections("about"),
    }
    return render(request, "pages/about.html", context)


def contact_view(request):
    context = {
        "sections": get_page_sections("contact"),
    }
    return render(request, "pages/contact.html", context)