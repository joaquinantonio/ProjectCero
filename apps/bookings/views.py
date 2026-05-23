from datetime import timedelta

from django.db.models import Q
from django.shortcuts import redirect, render
from django.http import JsonResponse
from django.urls import reverse
from django.utils.dateparse import parse_datetime
from django.views.decorators.http import require_GET

from .availability import get_unavailable_blocks

from apps.events.models import Event

from .forms import (
    StudioBookingRequestForm,
    VenueBookingRequestForm,
)
from .models import BookingRequest
from .services import send_booking_confirmation, send_booking_notification
from .utils import generate_booking_reference


def booking_landing_view(request):
    return render(request, "bookings/booking_landing.html")


def _handle_booking_request(
    request,
    request_type,
    form_class,
    page_title,
    intro_text,
    template_name="bookings/booking_form.html",
    extra_context=None,
):
    if request.method == "POST":
        form = form_class(request.POST)
        if form.is_valid():
            booking = form.save(commit=False)
            booking.request_type = request_type
            booking.save()

            booking.reference_code = generate_booking_reference(booking.id)
            booking.save(update_fields=["reference_code"])

            send_booking_notification(booking)
            send_booking_confirmation(booking)

            request.session["last_booking_reference"] = booking.reference_code
            return redirect("bookings:success")

        elif request.POST.get("website"):
            return redirect("bookings:success")
    else:
        form = form_class()

    context = {
        "form": form,
        "request_type": request_type,
        "page_title": page_title,
        "intro_text": intro_text,
    }

    if extra_context:
        context.update(extra_context)

    return render(request, template_name, context)


def general_booking_request_view(request):
    return redirect("enquiries:general")


def studio_booking_request_view(request):
    return _handle_booking_request(
        request=request,
        request_type=BookingRequest.RequestType.STUDIO,
        form_class=StudioBookingRequestForm,
        page_title="Studio Request",
        intro_text="Send a request for recording, rehearsal, or other studio-related work.",
        extra_context={
            "show_availability_calendar": True,
            "availability_title": "Check Studio Availability",
            "availability_note": (
                "Business hours are 11:00 AM to 12:00 midnight. "
                "Unavailable blocks may include confirmed bookings or events."
            ),
            "availability_feed_url": reverse("bookings:booking_unavailable_feed"),
        },
    )


def venue_booking_request_view(request):
    return _handle_booking_request(
        request=request,
        request_type=BookingRequest.RequestType.VENUE,
        form_class=VenueBookingRequestForm,
        page_title="Venue Request",
        intro_text="Use this form for event enquiries, venue hire, or private function discussions.",
        extra_context={
            "show_availability_calendar": True,
            "availability_title": "Check Venue Availability",
            "availability_note": (
                "Unavailable blocks may include confirmed bookings or scheduled events. "
                "Events block out the venue during their scheduled time."
            ),
            "availability_feed_url": reverse("bookings:booking_unavailable_feed"),
        },
    )


def booking_success_view(request):
    reference_code = request.session.get("last_booking_reference")
    return render(
        request,
        "bookings/booking_success.html",
        {"reference_code": reference_code},
    )

@require_GET
def studio_unavailable_feed_view(request):
    start_raw = request.GET.get("start")
    end_raw = request.GET.get("end")

    start_dt = parse_datetime(start_raw) if start_raw else None
    end_dt = parse_datetime(end_raw) if end_raw else None

    unavailable_items = []

    # Confirmed studio bookings
    booking_qs = BookingRequest.objects.filter(
        request_type=BookingRequest.RequestType.STUDIO,
        status=BookingRequest.Status.CONFIRMED,
        scheduled_start_at__isnull=False,
        scheduled_end_at__isnull=False,
    )

    if start_dt and end_dt:
        booking_qs = booking_qs.filter(
            scheduled_start_at__lt=end_dt,
            scheduled_end_at__gt=start_dt,
        )

    for booking in booking_qs:
        unavailable_items.append(
            {
                "title": "Unavailable",
                "start": booking.scheduled_start_at.isoformat(),
                "end": booking.scheduled_end_at.isoformat(),
                "classNames": ["public-unavailable-block"],
            }
        )

    # Events also block the space.
    # Public users only see "Unavailable", not event/admin details.
    event_qs = Event.objects.exclude(status=Event.Status.CANCELLED)

    if start_dt and end_dt:
        event_qs = event_qs.filter(start_at__lt=end_dt).filter(
            Q(end_at__gt=start_dt)
            | Q(end_at__isnull=True, start_at__gte=start_dt)
        )

    for event in event_qs:
        event_end = event.end_at or event.start_at + timedelta(hours=2)

        unavailable_items.append(
            {
                "title": "Unavailable",
                "start": event.start_at.isoformat(),
                "end": event_end.isoformat(),
                "classNames": ["public-unavailable-block"],
            }
        )

    return JsonResponse(unavailable_items, safe=False)

@require_GET
def booking_unavailable_feed_view(request):
    start_raw = request.GET.get("start")
    end_raw = request.GET.get("end")

    start_dt = parse_datetime(start_raw) if start_raw else None
    end_dt = parse_datetime(end_raw) if end_raw else None

    unavailable_items = []

    for block in get_unavailable_blocks(start_dt=start_dt, end_dt=end_dt):
        unavailable_items.append(
            {
                "title": "Unavailable",
                "start": block["start"].isoformat(),
                "end": block["end"].isoformat(),
                "classNames": ["public-unavailable-block"],
            }
        )

    return JsonResponse(unavailable_items, safe=False)