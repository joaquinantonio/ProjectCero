from django.conf import settings
from django.core.mail import send_mail


def send_enquiry_notification(enquiry):
    recipient = (
        getattr(settings, "ENQUIRY_NOTIFICATION_EMAIL", "")
        or getattr(settings, "BOOKING_NOTIFICATION_EMAIL", "")
    )

    if not recipient:
        return

    subject = (
        f"[{enquiry.reference_code}] "
        f"New {enquiry.get_enquiry_type_display()} enquiry from {enquiry.name}"
    )

    body = f"""
A new enquiry has been submitted.

Reference: {enquiry.reference_code}
Type: {enquiry.get_enquiry_type_display()}
Name: {enquiry.name}
Email: {enquiry.email}
Phone: {enquiry.phone or "-"}
Subject: {enquiry.subject}
Preferred date: {enquiry.preferred_date or "-"}
Related event: {enquiry.related_event or "-"}
Related merch: {enquiry.related_merch or "-"}
Amount / package: {enquiry.amount_text or "-"}
Created at: {enquiry.created_at}

Message:
{enquiry.message}
""".strip()

    send_mail(
        subject=subject,
        message=body,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[recipient],
        fail_silently=False,
    )