from dataclasses import dataclass, field

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.mail import send_mail

from .models import Booking, BookingRequest


def format_time(value):
    if not value:
        return "-"

    return value.strftime("%I:%M %p").lstrip("0")


def format_date(value):
    if not value:
        return "-"

    return value.strftime("%d %b %Y")


def get_booking_service_line(booking_request):
    studio_service = getattr(booking_request, "studio_service", None)

    if studio_service:
        return f"Studio service: {studio_service.name}"

    if booking_request.request_type == BookingRequest.RequestType.STUDIO:
        return "Studio service: Not selected"

    return None


def get_booking_summary_lines(booking_request):
    lines = [
        f"Reference: {booking_request.reference_code}",
        f"Type: {booking_request.get_request_type_display()}",
    ]

    service_line = get_booking_service_line(booking_request)
    if service_line:
        lines.append(service_line)

    lines.extend(
        [
            f"Name: {booking_request.name}",
            f"Email: {booking_request.email}",
            f"Phone: {booking_request.phone or '-'}",
            f"Preferred date: {format_date(booking_request.preferred_date)}",
            f"Preferred start time: {format_time(booking_request.preferred_start_time)}",
            f"Preferred end time: {format_time(booking_request.preferred_end_time)}",
            f"Guest count: {booking_request.guest_count or '-'}",
        ]
    )

    return "\n".join(lines)

def mark_request_as_booking_created(booking_request):
    if not booking_request:
        return False

    if booking_request.status == BookingRequest.Status.CONVERTED:
        return False

    booking_request.status = BookingRequest.Status.CONVERTED
    booking_request.save(update_fields=["status", "updated_at"])

    return True


def sync_request_status_after_booking_save(booking):
    if not booking or not booking.request_id:
        return False

    return mark_request_as_booking_created(booking.request)

def assign_default_booking_resource(booking):
    if not booking or booking.resource_id:
        return False

    from .calendar_workflow import get_default_booking_resource

    default_resource = get_default_booking_resource()
    if not default_resource:
        return False

    booking.resource = default_resource
    return True


def prepare_booking_for_save(booking):
    return assign_default_booking_resource(booking)

@dataclass
class BookingStatusUpdateResult:
    updated: int = 0
    skipped: int = 0
    errors: list[str] = field(default_factory=list)


def get_validation_error_message(exc):
    if hasattr(exc, "messages") and exc.messages:
        return exc.messages[0]

    return str(exc)


def update_booking_status(booking, target_status):
    original_status = booking.status
    booking.status = target_status

    try:
        if target_status in Booking.BLOCKING_STATUSES:
            booking.full_clean()

        booking.save(update_fields=["status", "updated_at"])

    except ValidationError:
        booking.status = original_status
        raise

    return booking


def bulk_update_booking_statuses(bookings, target_status):
    result = BookingStatusUpdateResult()

    for booking in bookings:
        try:
            update_booking_status(booking, target_status)
            result.updated += 1

        except ValidationError as exc:
            result.skipped += 1
            error_text = get_validation_error_message(exc)
            result.errors.append(f"{booking.reference_code}: {error_text}")

    return result

def send_booking_notification(booking_request):
    if not settings.BOOKING_NOTIFICATION_EMAIL:
        return

    subject = (
        f"[{booking_request.reference_code}] "
        f"New {booking_request.get_request_type_display()} request from {booking_request.name}"
    )

    body = f"""
A new booking request has been submitted.

This is a customer request only. It does not block the calendar until an admin creates a linked Booking record.

{get_booking_summary_lines(booking_request)}
Created at: {booking_request.created_at}

Message:
{booking_request.message}
""".strip()

    send_mail(
        subject=subject,
        message=body,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[settings.BOOKING_NOTIFICATION_EMAIL],
        fail_silently=False,
    )


def send_booking_confirmation(booking_request):
    subject = f"We received your booking request ({booking_request.reference_code})"

    body = f"""
Hi {booking_request.name},

Thanks for getting in touch. We've received your {booking_request.get_request_type_display().lower()} request.

Important: this is not a confirmed booking yet. Our team will review your preferred date and time, then contact you to confirm availability and next steps.

{get_booking_summary_lines(booking_request)}

Message received:
{booking_request.message}

Please keep your reference number in case you need to follow up:
{booking_request.reference_code}

Regards,
CeroPJ
""".strip()

    send_mail(
        subject=subject,
        message=body,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[booking_request.email],
        fail_silently=False,
    )