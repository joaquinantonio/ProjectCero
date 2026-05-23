from datetime import timedelta

from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models
from django.utils import timezone
from uuid import uuid4

from apps.core.models import TimeStampedModel


class BookingRequest(TimeStampedModel):
    def clean(self):
        super().clean()

        errors = {}

        is_confirmed_studio_booking = (
                self.request_type == self.RequestType.STUDIO
                and self.status == self.Status.CONFIRMED
        )

        # Confirmed studio bookings must have a real schedule block.
        if is_confirmed_studio_booking and not self.scheduled_start_at:
            errors["scheduled_start_at"] = (
                "A confirmed studio booking must have a scheduled start time."
            )

        if is_confirmed_studio_booking and not self.scheduled_end_at:
            errors["scheduled_end_at"] = (
                "A confirmed studio booking must have a scheduled end time."
            )

        # If one scheduled time is provided, both must be provided.
        if bool(self.scheduled_start_at) != bool(self.scheduled_end_at):
            errors["scheduled_start_at"] = (
                "Both scheduled start time and scheduled end time must be provided together."
            )
            errors["scheduled_end_at"] = (
                "Both scheduled start time and scheduled end time must be provided together."
            )

        if errors:
            raise ValidationError(errors)

        # If there is no schedule block yet, stop here.
        if not self.scheduled_start_at or not self.scheduled_end_at:
            return

        # End must be after start.
        if self.scheduled_end_at <= self.scheduled_start_at:
            raise ValidationError(
                {
                    "scheduled_end_at": (
                        "Scheduled end time must be after scheduled start time."
                    )
                }
            )

        # Business hours validation only applies to studio bookings.
        if self.request_type == self.RequestType.STUDIO:
            local_start = timezone.localtime(self.scheduled_start_at)
            local_end = timezone.localtime(self.scheduled_end_at)

            business_start = local_start.replace(
                hour=11,
                minute=0,
                second=0,
                microsecond=0,
            )
            business_end = business_start + timedelta(hours=13)  # 11 AM to 12 midnight

            if not (business_start <= local_start < business_end):
                errors["scheduled_start_at"] = (
                    "Studio booking must start within business hours: "
                    "11:00 AM to 12:00 midnight."
                )

            if not (business_start < local_end <= business_end):
                errors["scheduled_end_at"] = (
                    "Studio booking must end within business hours: "
                    "11:00 AM to 12:00 midnight."
                )

        if errors:
            raise ValidationError(errors)

        # Overlap validation only applies to confirmed studio bookings.
        if not is_confirmed_studio_booking:
            return

        overlapping_booking = (
            BookingRequest.objects.filter(
                request_type=self.RequestType.STUDIO,
                status=self.Status.CONFIRMED,
                scheduled_start_at__lt=self.scheduled_end_at,
                scheduled_end_at__gt=self.scheduled_start_at,
            )
            .exclude(pk=self.pk)
            .order_by("scheduled_start_at")
            .first()
        )

        if overlapping_booking:
            overlap_start = timezone.localtime(overlapping_booking.scheduled_start_at)
            overlap_end = timezone.localtime(overlapping_booking.scheduled_end_at)

            raise ValidationError(
                {
                    "scheduled_start_at": (
                        f"This booking overlaps with confirmed studio booking "
                        f"{overlapping_booking.reference_code} "
                        f"from {overlap_start:%d %b %Y, %I:%M %p} "
                        f"to {overlap_end:%I:%M %p}."
                    )
                }
            )

    def generate_reference_code(self):
        while True:
            reference_code = f"BK-{uuid4().hex[:8].upper()}"

            exists = BookingRequest.objects.filter(
                reference_code=reference_code
            ).exclude(pk=self.pk).exists()

            if not exists:
                return reference_code

    def save(self, *args, **kwargs):
        if not self.reference_code:
            self.reference_code = self.generate_reference_code()

            update_fields = kwargs.get("update_fields")
            if update_fields is not None:
                kwargs["update_fields"] = set(update_fields) | {"reference_code"}

        super().save(*args, **kwargs)

    class RequestType(models.TextChoices):
        GENERAL = "general", "General"
        STUDIO = "studio", "Studio"
        VENUE = "venue", "Venue"
        PRIVATE_EVENT = "private_event", "Private Event"

    class Status(models.TextChoices):
        NEW = "new", "New"
        IN_REVIEW = "in_review", "In Review"
        CONTACTED = "contacted", "Contacted"
        CONFIRMED = "confirmed", "Confirmed"
        CLOSED = "closed", "Closed"
        CANCELLED = "cancelled", "Cancelled"

    reference_code = models.CharField(max_length=32, unique=True, blank=True)

    event = models.ForeignKey(
        "events.Event",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="booking_requests",
    )
    request_type = models.CharField(
        max_length=20,
        choices=RequestType.choices,
    )
    name = models.CharField(max_length=150)
    email = models.EmailField()
    phone = models.CharField(max_length=50, blank=True)
    preferred_date = models.DateField(blank=True, null=True)
    preferred_time = models.TimeField(blank=True, null=True)
    scheduled_start_at = models.DateTimeField(
        blank=True,
        null=True,
        help_text="Confirmed internal start time. Used for the schedule calendar.",
    )
    scheduled_end_at = models.DateTimeField(
        blank=True,
        null=True,
        help_text="Confirmed internal end time. Used for the schedule calendar.",
    )
    guest_count = models.PositiveIntegerField(
        blank=True,
        null=True,
        validators=[MinValueValidator(1)],
    )
    message = models.TextField()
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.NEW,
    )
    admin_notes = models.TextField(blank=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["status", "created_at"]),
            models.Index(fields=["request_type", "created_at"]),
            models.Index(fields=["event"]),
            models.Index(fields=["reference_code"]),
        ]

    def __str__(self):
        return self.reference_code or f"{self.name} - {self.request_type}"

class ScheduleCalendar(BookingRequest):
    class Meta:
        proxy = True
        verbose_name = "Admin Calendar"
        verbose_name_plural = "Admin Calendar"