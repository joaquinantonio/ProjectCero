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


def send_artist_enquiry_notification(artist_enquiry):
    """Send notification about new artist enquiry to admin."""
    recipient = (
        getattr(settings, "ENQUIRY_NOTIFICATION_EMAIL", "")
        or getattr(settings, "BOOKING_NOTIFICATION_EMAIL", "")
    )

    if not recipient:
        return

    subject = (
        f"[{artist_enquiry.reference_code}] "
        f"New artist enquiry for {artist_enquiry.related_artist.name} from {artist_enquiry.name}"
    )

    body = f"""
A new artist enquiry has been submitted.

Reference: {artist_enquiry.reference_code}
Artist: {artist_enquiry.related_artist.name}
Name: {artist_enquiry.name}
Email: {artist_enquiry.email}
Phone: {artist_enquiry.phone}
Status: {artist_enquiry.get_status_display()}
Created at: {artist_enquiry.created_at}

Action:
Review the enquiry in admin and contact {artist_enquiry.name} by phone or WhatsApp at {artist_enquiry.phone}.
""".strip()

    send_mail(
        subject=subject,
        message=body,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[recipient],
        fail_silently=False,
    )
