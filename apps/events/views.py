from django.db.models import Q
from django.http import Http404, HttpResponse, JsonResponse
from django.shortcuts import render
from django.utils.dateparse import parse_datetime
from django.views.decorators.http import require_GET
from apps.core.utils import paginate_queryset
from icalendar import Calendar, Event as ICalEvent
from .models import EventCategory
from .selectors import (
    get_calendar_events_between,
    get_past_events,
    get_published_event_by_slug,
    get_related_upcoming_events,
    get_upcoming_events,
)

def event_list_view(request):
    upcoming_events = get_upcoming_events()
    past_events = get_past_events(limit=6)
    categories = EventCategory.objects.active().order_by("sort_order", "name")

    category_slug = request.GET.get("category", "").strip()
    search_query = request.GET.get("q", "").strip()
    selected_category = None

    if category_slug:
        selected_category = categories.filter(slug=category_slug).first()
        if selected_category:
            upcoming_events = upcoming_events.filter(category=selected_category)

    if search_query:
        upcoming_events = upcoming_events.filter(
            Q(title__icontains=search_query) |
            Q(short_description__icontains=search_query) |
            Q(description__icontains=search_query) |
            Q(location_text__icontains=search_query)
        )

    upcoming_page = paginate_queryset(request, upcoming_events, per_page=6)

    return render(
        request,
        "events/event_list.html",
        {
            "upcoming_events": upcoming_page,
            "past_events": past_events,
            "categories": categories,
            "selected_category": selected_category,
            "search_query": search_query,
        },
    )


def past_event_list_view(request):
    past_events = get_past_events()
    return render(
        request,
        "events/past_event_list.html",
        {
            "past_events": past_events,
        },
    )



def event_detail_view(request, slug):
    try:
        event = get_published_event_by_slug(slug)
    except Exception:
        raise Http404("Event not found")

    ordered_event_artists = event.event_artists.all()
    related_events = get_related_upcoming_events(event, limit=3)

    return render(
        request,
        "events/event_detail.html",
        {
            "event": event,
            "ordered_event_artists": ordered_event_artists,
            "related_events": related_events,
        },
    )


def event_calendar_view(request):
    return render(request, "events/calendar.html")


@require_GET
def event_calendar_feed_view(request):
    start_raw = request.GET.get("start")
    end_raw = request.GET.get("end")

    start_dt = parse_datetime(start_raw) if start_raw else None
    end_dt = parse_datetime(end_raw) if end_raw else None

    events = get_calendar_events_between(start_dt=start_dt, end_dt=end_dt)

    data = []
    for event in events:
        data.append({
            "title": event.title,
            "start": event.start_at.isoformat(),
            "end": event.end_at.isoformat() if event.end_at else None,
            "url": f"/events/{event.slug}/",
        })

    return JsonResponse(data, safe=False)


@require_GET
def event_ics_feed_view(request):
    cal = Calendar()
    cal.add("prodid", "-//CeroPJ//Events Calendar//EN")
    cal.add("version", "2.0")

    events = get_upcoming_events()

    for item in events:
        e = ICalEvent()
        e.add("summary", item.title)
        e.add("dtstart", item.start_at)
        if item.end_at:
            e.add("dtend", item.end_at)
        e.add("description", item.description or "")
        e.add("location", item.location_text or "")
        e.add("uid", f"event-{item.id}@CeroPJ.local")
        cal.add_component(e)

    response = HttpResponse(cal.to_ical(), content_type="text/calendar")
    response["Content-Disposition"] = 'attachment; filename="events.ics"'
    return response


@require_GET
def single_event_ics_feed_view(request, slug):
    try:
        item = get_published_event_by_slug(slug)
    except Exception:
        raise Http404("Event not found")

    cal = Calendar()
    cal.add("prodid", "-//CeroPJ//Single Event Calendar//EN")
    cal.add("version", "2.0")

    e = ICalEvent()
    e.add("summary", item.title)
    e.add("dtstart", item.start_at)
    if item.end_at:
        e.add("dtend", item.end_at)
    e.add("description", item.description or "")
    e.add("location", item.location_text or "")
    e.add("uid", f"event-{item.id}@CeroPJ.local")
    cal.add_component(e)

    response = HttpResponse(cal.to_ical(), content_type="text/calendar")
    response["Content-Disposition"] = f'attachment; filename="{item.slug}.ics"'
    return response