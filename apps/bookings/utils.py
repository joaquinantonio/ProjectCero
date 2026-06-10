from django.utils import timezone


def generate_booking_reference(booking_id: int) -> str:
    today = timezone.localdate()
    return f"BK-{today:%Y%m%d}-{booking_id:05d}"