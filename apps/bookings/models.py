from django.core.validators import MinValueValidator
from django.db import models
from datetime import timedelta

from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models
from django.utils import timezone

from apps.core.models import TimeStampedModel


class BookingRequest(TimeStampedModel):
    def clean(self):
        super().clean()

        if bool(self.scheduled_start_at) != bool(self.scheduled_end_at):
            raise ValidationError(
                "Both scheduled start time and scheduled end time must be provided together."
            )

        if not self.scheduled_start_at or not self.scheduled_end_at:
            return

        if self.scheduled_end_at <= self.scheduled_start_at:
            raise ValidationError(
                "Scheduled end time must be after scheduled start time."
            )

        local_start = timezone.localtime(self.scheduled_start_at)
        local_end = timezone.localtime(self.scheduled_end_at)

        business_start = local_start.replace(
            hour=11,
            minute=0,
            second=0,
            microsecond=0,
        )
        business_end = business_start.replace(hour=0) + timedelta(days=1)

        if not (business_start <= local_start < business_end):
            raise ValidationError(
                "Studio booking must start within business hours: 11:00 AM to 12:00 midnight."
            )

        if not (business_start < local_end <= business_end):
            raise ValidationError(
                "Studio booking must end within business hours: 11:00 AM to 12:00 midnight."
            )
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