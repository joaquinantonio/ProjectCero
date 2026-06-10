from django.conf import settings
from django.core.mail import send_mail

from .models import BookingRequest


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