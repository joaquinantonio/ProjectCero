from uuid import uuid4

from django.db import migrations
from django.db.models import F


def generate_booking_reference(Booking):
    while True:
        reference_code = f"BKG-{uuid4().hex[:8].upper()}"

        if not Booking.objects.filter(reference_code=reference_code).exists():
            return reference_code


def forwards(apps, schema_editor):
    BookingRequest = apps.get_model("bookings", "BookingRequest")
    BookingResource = apps.get_model("bookings", "BookingResource")
    Booking = apps.get_model("bookings", "Booking")

    resource, _ = BookingResource.objects.get_or_create(
        slug="ceropj-venue",
        defaults={
            "name": "CeroPJ Venue",
            "description": "Main ProjectCero venue resource.",
            "is_active": True,
            "display_order": 0,
        },
    )

    booking_type_map = {
        "studio": "studio",
        "venue": "venue",
        "private_event": "venue",
    }

    scheduled_requests = BookingRequest.objects.filter(
        scheduled_start_at__isnull=False,
        scheduled_end_at__isnull=False,
        scheduled_end_at__gt=F("scheduled_start_at"),
        request_type__in=["studio", "venue", "private_event"],
    )

    for booking_request in scheduled_requests:
        if Booking.objects.filter(request=booking_request).exists():
            continue

        original_request_type = booking_request.request_type

        if booking_request.status == "confirmed":
            booking_status = "confirmed"
        elif booking_request.status == "cancelled":
            booking_status = "cancelled"
        else:
            booking_status = "tentative"

        internal_notes = booking_request.admin_notes

        if original_request_type == "private_event":
            migration_note = (
                "Legacy private_event request migrated as venue booking."
            )
            internal_notes = (
                f"{migration_note}\n\n{internal_notes}"
                if internal_notes
                else migration_note
            )

        Booking.objects.create(
            reference_code=generate_booking_reference(Booking),
            request=booking_request,
            resource=resource,
            booking_type=booking_type_map[original_request_type],
            title=booking_request.name,
            scheduled_start_at=booking_request.scheduled_start_at,
            scheduled_end_at=booking_request.scheduled_end_at,
            status=booking_status,
            internal_notes=internal_notes,
        )

    legacy_private_event_requests = BookingRequest.objects.filter(
        request_type="private_event"
    )

    for booking_request in legacy_private_event_requests:
        if booking_request.admin_notes:
            booking_request.admin_notes = (
                "Legacy private_event request converted to venue request.\n\n"
                f"{booking_request.admin_notes}"
            )
        else:
            booking_request.admin_notes = (
                "Legacy private_event request converted to venue request."
            )

        booking_request.request_type = "venue"
        booking_request.save(
            update_fields=[
                "request_type",
                "admin_notes",
                "updated_at",
            ]
        )


def backwards(apps, schema_editor):
    Booking = apps.get_model("bookings", "Booking")

    Booking.objects.filter(request__isnull=False).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("bookings", "0005_booking_bookingresource_and_more"),
    ]

    operations = [
        migrations.RunPython(forwards, backwards),
    ]