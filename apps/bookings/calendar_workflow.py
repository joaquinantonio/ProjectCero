from datetime import datetime, timedelta

from django.core.exceptions import ValidationError
from django.utils import timezone

from .models import Booking, BookingRequest, BookingResource


DEFAULT_BOOKING_DURATIONS = {
    BookingRequest.RequestType.STUDIO: timedelta(hours=2),
    BookingRequest.RequestType.VENUE: timedelta(hours=4),
}


def get_default_booking_resource():
    """
    Return the default physical resource for calendar-blocking bookings.

    For current ProjectCero operations there is normally one physical resource:
    the CeroPJ venue/space. Studio and venue are represented by booking_type.
    """
    return (
        BookingResource.objects.filter(is_active=True)
        .order_by("display_order", "name", "id")
        .first()
        or BookingResource.objects.order_by("display_order", "name", "id").first()
    )


def request_type_to_booking_type(request_type):
    if request_type == BookingRequest.RequestType.STUDIO:
        return Booking.BookingType.STUDIO

    if request_type == BookingRequest.RequestType.VENUE:
        return Booking.BookingType.VENUE

    return None


def build_request_start_at(booking_request):
    if not booking_request.preferred_date or not booking_request.preferred_start_time:
        return None

    naive_start = datetime.combine(
        booking_request.preferred_date,
        booking_request.preferred_start_time,
    )

    current_timezone = timezone.get_current_timezone()

    if timezone.is_naive(naive_start):
        return timezone.make_aware(naive_start, current_timezone)

    return naive_start


def get_booking_initial_from_request(booking_request):
    """
    Build safe initial values for the Booking add form from a public request.
    Admins can still adjust exact date/time before saving.
    """
    booking_type = request_type_to_booking_type(booking_request.request_type)
    start_at = build_request_start_at(booking_request)
    duration = DEFAULT_BOOKING_DURATIONS.get(
        booking_request.request_type,
        timedelta(hours=2),
    )
    end_at = start_at + duration if start_at else None
    default_resource = get_default_booking_resource()

    initial = {
        "request": booking_request.pk,
        "booking_type": booking_type,
        "title": f"{booking_request.name} ({booking_request.get_request_type_display()})",
        "status": Booking.Status.CONFIRMED,
    }

    if default_resource:
        initial["resource"] = default_resource.pk

    if start_at:
        initial["scheduled_start_at"] = start_at
        initial["scheduled_end_at"] = end_at

    return {key: value for key, value in initial.items() if value is not None}


def create_calendar_booking_from_request(
    booking_request,
    *,
    status=Booking.Status.CONFIRMED,
):
    """
    Create a calendar-blocking Booking from a BookingRequest.

    Returns:
        (booking, message)

    A BookingRequest by itself is intake only and does not block calendars.
    This helper turns an admin-confirmed request into a real Booking record.
    """
    if booking_request.bookings.exists():
        return (
            booking_request.bookings.order_by("scheduled_start_at", "id").first(),
            "A calendar booking already exists for this request.",
        )

    booking_type = request_type_to_booking_type(booking_request.request_type)
    if not booking_type:
        return None, "Only Studio and Venue requests can become calendar bookings."

    start_at = build_request_start_at(booking_request)
    if not start_at:
        return (
            None,
            "Preferred date and preferred time are required before a calendar booking can be created.",
        )

    default_resource = get_default_booking_resource()
    if not default_resource:
        return (
            None,
            "No active booking resource exists. Create one Booking Resource first, for example 'CeroPJ Venue'.",
        )

    duration = DEFAULT_BOOKING_DURATIONS.get(
        booking_request.request_type,
        timedelta(hours=2),
    )
    end_at = start_at + duration

    booking = Booking(
        request=booking_request,
        resource=default_resource,
        booking_type=booking_type,
        title=f"{booking_request.name} ({booking_request.get_request_type_display()})",
        scheduled_start_at=start_at,
        scheduled_end_at=end_at,
        status=status,
    )

    try:
        booking.full_clean()
    except ValidationError as exc:
        return None, f"Calendar booking was not created: {exc.messages[0] if exc.messages else exc}"

    booking.save()
    return (
        booking,
        (
            "Calendar booking created. "
            "Review the generated start/end time and adjust the Booking record if needed."
        ),
    )
