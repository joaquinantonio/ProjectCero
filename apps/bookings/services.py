from django.conf import settings
from django.core.mail import send_mail


def get_booking_service_line(booking):
    if booking.studio_service:
        return f"Studio service: {booking.studio_service.name}"
    return "Studio service: -"


def send_booking_notification(booking):
    if not settings.BOOKING_NOTIFICATION_EMAIL:
        return

    subject = f"[{booking.reference_code}] New {booking.get_request_type_display()} request from {booking.name}"

    body = f"""
A new booking request has been submitted.

Reference: {booking.reference_code}
Type: {booking.get_request_type_display()}
{get_booking_service_line(booking)}
Name: {booking.name}
Email: {booking.email}
Phone: {booking.phone or "-"}
Preferred date: {booking.preferred_date or "-"}
Preferred time: {booking.preferred_time or "-"}
Guest count: {booking.guest_count or "-"}
Created at: {booking.created_at}

Message:
{booking.message}
""".strip()

    send_mail(
        subject=subject,
        message=body,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[settings.BOOKING_NOTIFICATION_EMAIL],
        fail_silently=False,
    )


def send_booking_confirmation(booking):
    subject = f"We received your request ({booking.reference_code})"

    body = f"""
Hi {booking.name},

Thanks for getting in touch. We’ve received your {booking.get_request_type_display().lower()} request.

Reference: {booking.reference_code}
Type: {booking.get_request_type_display()}
{get_booking_service_line(booking)}
Preferred date: {booking.preferred_date or "-"}
Preferred time: {booking.preferred_time or "-"}
Guest count: {booking.guest_count or "-"}

We’ll review your request and get back to you soon.

Message received:
{booking.message}

Regards,
{settings.DEFAULT_FROM_EMAIL}
""".strip()

    send_mail(
        subject=subject,
        message=body,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[booking.email],
        fail_silently=False,
    )