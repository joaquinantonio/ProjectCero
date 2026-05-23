from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils.dateparse import parse_datetime
from django.views.decorators.http import require_GET

from .availability import get_unavailable_blocks
from .forms import CombinedBookingRequestForm
from .models import BookingRequest
from .services import send_booking_confirmation, send_booking_notification


def booking_landing_view(request):
    return render(request, "bookings/booking_landing.html")


def general_booking_request_view(request):
    return redirect("enquiries:general")


def booking_request_view(request):
    allowed_types = [
        BookingRequest.RequestType.STUDIO,
        BookingRequest.RequestType.VENUE,
    ]

    initial_type = request.GET.get("type")

    if initial_type not in allowed_types:
        initial_type = BookingRequest.RequestType.STUDIO

    if request.method == "POST":
        form = CombinedBookingRequestForm(request.POST)

        if form.is_valid():
            booking = form.save(commit=False)
            booking.save()

            send_booking_notification(booking)
            send_booking_confirmation(booking)

            request.session["last_booking_reference"] = booking.reference_code
            return redirect("bookings:success")

        elif request.POST.get("website"):
            return redirect("bookings:success")

    else:
        form = CombinedBookingRequestForm(
            initial={
                "request_type": initial_type,
            }
        )

    return render(
        request,
        "bookings/booking_form.html",
        {
            "form": form,
            "request_type": "combined",
            "page_title": "Booking Request",
            "intro_text": (
                "Request a studio session or venue booking. "
                "Check availability first, then send us your preferred details."
            ),
            "show_availability_calendar": True,
            "availability_title": "Check Availability",
            "availability_note": (
                "Unavailable blocks may include confirmed studio bookings, "
                "venue bookings, private events, or scheduled events."
            ),
            "availability_feed_url": reverse("bookings:booking_unavailable_feed"),
        },
    )


def studio_booking_request_view(request):
    return redirect(f"{reverse('bookings:request')}?type=studio")


def venue_booking_request_view(request):
    return redirect(f"{reverse('bookings:request')}?type=venue")


def booking_success_view(request):
    reference_code = request.session.get("last_booking_reference")
    return render(
        request,
        "bookings/booking_success.html",
        {"reference_code": reference_code},
    )


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