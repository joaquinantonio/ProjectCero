from datetime import timedelta

from django.db.models import Q
from django.utils import timezone

from apps.events.models import Event
from .models import BookingRequest


EVENT_FALLBACK_DURATION = timedelta(hours=2)


def get_event_blocks(start_dt=None, end_dt=None):
    qs = Event.objects.exclude(status=Event.Status.CANCELLED)

    if start_dt and end_dt:
        qs = qs.filter(start_at__lt=end_dt).filter(
            Q(end_at__gt=start_dt)
            | Q(end_at__isnull=True, start_at__gte=start_dt)
        )

    blocks = []

    for event in qs:
        event_end = event.end_at or event.start_at + EVENT_FALLBACK_DURATION

        blocks.append(
            {
                "type": "event",
                "object": event,
                "start": event.start_at,
                "end": event_end,
            }
        )

    return blocks


def get_confirmed_booking_blocks(start_dt=None, end_dt=None, exclude_booking_id=None):
    qs = BookingRequest.objects.filter(
        status=BookingRequest.Status.CONFIRMED,
        scheduled_start_at__isnull=False,
        scheduled_end_at__isnull=False,
    )

    if exclude_booking_id:
        qs = qs.exclude(pk=exclude_booking_id)

    if start_dt and end_dt:
        qs = qs.filter(
            scheduled_start_at__lt=end_dt,
            scheduled_end_at__gt=start_dt,
        )

    blocks = []

    for booking in qs:
        blocks.append(
            {
                "type": "booking",
                "object": booking,
                "start": booking.scheduled_start_at,
                "end": booking.scheduled_end_at,
            }
        )

    return blocks


def get_unavailable_blocks(start_dt=None, end_dt=None, exclude_booking_id=None):
    """
    V1 rule:
    - events block both studio and venue
    - confirmed bookings block availability
    - public users only see 'Unavailable'
    """
    return [
        *get_event_blocks(start_dt=start_dt, end_dt=end_dt),
        *get_confirmed_booking_blocks(
            start_dt=start_dt,
            end_dt=end_dt,
            exclude_booking_id=exclude_booking_id,
        ),
    ]


def find_conflicting_block(start_at, end_at, exclude_booking_id=None):
    if not start_at or not end_at:
        return None

    blocks = get_unavailable_blocks(
        start_dt=start_at,
        end_dt=end_at,
        exclude_booking_id=exclude_booking_id,
    )

    return blocks[0] if blocks else None


def format_block_time(start_at, end_at):
    local_start = timezone.localtime(start_at)
    local_end = timezone.localtime(end_at)

    return f"{local_start:%d %b %Y, %I:%M %p} to {local_end:%I:%M %p}"


def build_conflict_message(block):
    block_time = format_block_time(block["start"], block["end"])

    if block["type"] == "event":
        event = block["object"]
        return f"This booking overlaps with event '{event.title}' from {block_time}."

    booking = block["object"]
    return (
        f"This booking overlaps with confirmed booking "
        f"{booking.reference_code} from {block_time}."
    )