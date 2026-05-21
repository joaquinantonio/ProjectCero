from django.core.validators import MinValueValidator
from django.db import models

from apps.core.models import TimeStampedModel


class BookingRequest(TimeStampedModel):
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