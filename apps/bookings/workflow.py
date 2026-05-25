from datetime import datetime

from django.utils import timezone

from .models import Booking, BookingRequest, BookingResource


def get_booking_type_from_request(booking_request):
    if booking_request.request_type == BookingRequest.RequestType.VENUE:
        return Booking.BookingType.VENUE

    return Booking.BookingType.STUDIO


def get_request_start_at(booking_request):
    if not booking_request.preferred_date or not booking_request.preferred_time:
        return None

    combined = datetime.combine(
        booking_request.preferred_date,
        booking_request.preferred_time,
    )

    if timezone.is_naive(combined):
        return timezone.make_aware(combined, timezone.get_current_timezone())

    return combined


def create_calendar_booking_from_request(
    booking_request,
    *,
    status=Booking.Status.CONFIRMED,
):
    """
    Create one calendar-blocking Booking from a BookingRequest.
    """
    existing_booking = booking_request.bookings.order_by("scheduled_start_at").first()
    if existing_booking:
        return existing_booking, "exists"

    start_at = get_request_start_at(booking_request)
    if not start_at:
        return None, "missing_datetime"

    booking_type = get_booking_type_from_request(booking_request)
    duration = Booking.default_duration_for_type(booking_type)
    end_at = start_at + duration

    service_name = ""
    if getattr(booking_request, "studio_service_id", None) and booking_request.studio_service:
        service_name = f"\nSelected studio service: {booking_request.studio_service.name}"

    booking = Booking(
        request=booking_request,
        resource=BookingResource.get_default_resource(),
        booking_type=booking_type,
        title=f"{booking_request.get_request_type_display()} - {booking_request.name}",
        scheduled_start_at=start_at,
        scheduled_end_at=end_at,
        status=status,
        internal_notes=(
            f"Auto-created from booking request {booking_request.reference_code}."
            f"\nDefault duration applied: {duration}."
            "\nAdjust start/end time if the final arrangement changes."
            f"{service_name}"
        ),
    )

    booking.full_clean()
    booking.save()

    return booking, "created"
