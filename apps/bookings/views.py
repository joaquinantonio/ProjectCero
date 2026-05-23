from django.shortcuts import redirect, render

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

    return render(
        request,
        template_name,
        {
            "form": form,
            "request_type": request_type,
            "page_title": page_title,
            "intro_text": intro_text,
        },
    )


def general_booking_request_view(request):
    return redirect("enquiries:general")


def studio_booking_request_view(request):
    return _handle_booking_request(
        request=request,
        request_type=BookingRequest.RequestType.STUDIO,
        form_class=StudioBookingRequestForm,
        page_title="Studio Request",
        intro_text="Send a request for recording, rehearsal, or other studio-related work.",
    )


def venue_booking_request_view(request):
    return _handle_booking_request(
        request=request,
        request_type=BookingRequest.RequestType.VENUE,
        form_class=VenueBookingRequestForm,
        page_title="Venue Request",
        intro_text="Use this form for event enquiries, venue hire, or private function discussions.",
    )


def booking_success_view(request):
    reference_code = request.session.get("last_booking_reference")
    return render(
        request,
        "bookings/booking_success.html",
        {"reference_code": reference_code},
    )