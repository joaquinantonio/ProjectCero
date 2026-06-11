from datetime import timedelta

from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models
from django.utils import timezone

from apps.core.models import ReferenceCodeMixin, SluggedModelMixin, TimeStampedModel


class BookingRequest(ReferenceCodeMixin, TimeStampedModel):
    reference_code_prefix = "BK"
    class RequestType(models.TextChoices):
        GENERAL = "general", "General"
        STUDIO = "studio", "Studio"
        VENUE = "venue", "Venue"

    class Status(models.TextChoices):
        NEW = "new", "New"
        IN_REVIEW = "in_review", "In Review"
        CONTACTED = "contacted", "Contacted"
        CONVERTED = "converted", "Booking Created"
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
    preferred_start_time = models.TimeField(blank=True, null=True)
    preferred_end_time = models.TimeField(blank=True, null=True)

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


class BookingResource(SluggedModelMixin, TimeStampedModel):
    """
    Physical bookable resource.

    For now, CeroPJ has one physical resource:
    CeroPJ Venue.

    Studio and venue are booking types/workflows, not separate physical resources.
    """

    slug_max_length = 170

    name = models.CharField(max_length=150)
    slug = models.SlugField(max_length=170, unique=True)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    display_order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["display_order", "name"]
        indexes = [
            models.Index(fields=["is_active", "display_order"]),
        ]

    def __str__(self):
        return self.name


class Booking(ReferenceCodeMixin, TimeStampedModel):
    reference_code_prefix = "BKG"
    BUSINESS_START_HOUR = 11
    BUSINESS_DURATION_HOURS = 13

    class BookingType(models.TextChoices):
        STUDIO = "studio", "Studio"
        VENUE = "venue", "Venue"

    class Status(models.TextChoices):
        TENTATIVE = "tentative", "Tentative"
        CONFIRMED = "confirmed", "Confirmed"
        CANCELLED = "cancelled", "Cancelled"
        COMPLETED = "completed", "Completed"
        NO_SHOW = "no_show", "No Show"

    BLOCKING_STATUSES = (
        Status.TENTATIVE,
        Status.CONFIRMED,
    )

    reference_code = models.CharField(max_length=32, unique=True, blank=True)

    request = models.ForeignKey(
        BookingRequest,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="bookings",
        help_text="Optional. Link this booking to the original public request.",
    )

    resource = models.ForeignKey(
        BookingResource,
        on_delete=models.PROTECT,
        related_name="bookings",
    )

    booking_type = models.CharField(
        max_length=30,
        choices=BookingType.choices,
    )

    title = models.CharField(
        max_length=200,
        blank=True,
        help_text="Optional internal title. If blank, the linked request name is used.",
    )

    scheduled_start_at = models.DateTimeField()
    scheduled_end_at = models.DateTimeField()

    status = models.CharField(
        max_length=30,
        choices=Status.choices,
        default=Status.TENTATIVE,
    )

    internal_notes = models.TextField(blank=True)

    class Meta:
        ordering = ["scheduled_start_at", "title", "id"]
        indexes = [
            models.Index(fields=["status", "scheduled_start_at"]),
            models.Index(fields=["status", "scheduled_end_at"]),
            models.Index(fields=["resource", "status", "scheduled_start_at"]),
            models.Index(fields=["booking_type", "status", "scheduled_start_at"]),
            models.Index(fields=["request"]),
            models.Index(fields=["reference_code"]),
        ]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(
                    scheduled_end_at__gt=models.F("scheduled_start_at")
                ),
                name="booking_scheduled_end_after_start",
            ),
        ]

    def clean(self):
        super().clean()

        errors = {}

        if not self.scheduled_start_at:
            errors["scheduled_start_at"] = "Scheduled start time is required."

        if not self.scheduled_end_at:
            errors["scheduled_end_at"] = "Scheduled end time is required."

        if not self.resource_id:
            errors["resource"] = "Booking resource is required."

        if errors:
            raise ValidationError(errors)

        if self.scheduled_end_at <= self.scheduled_start_at:
            errors["scheduled_end_at"] = (
                "Scheduled end time must be after scheduled start time."
            )

        if self.booking_type == self.BookingType.STUDIO:
            local_start = timezone.localtime(self.scheduled_start_at)
            local_end = timezone.localtime(self.scheduled_end_at)

            business_start = local_start.replace(
                hour=self.BUSINESS_START_HOUR,
                minute=0,
                second=0,
                microsecond=0,
            )
            business_end = business_start + timedelta(
                hours=self.BUSINESS_DURATION_HOURS
            )

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

        if self.status not in self.BLOCKING_STATUSES:
            return

        from .availability import build_conflict_message, find_conflicting_block

        conflict = find_conflicting_block(
            start_at=self.scheduled_start_at,
            end_at=self.scheduled_end_at,
            resource=self.resource,
            exclude_booking_id=self.pk,
        )

        if conflict:
            raise ValidationError(
                {
                    "scheduled_start_at": build_conflict_message(conflict),
                }
            )


    @property
    def display_title(self):
        if self.title:
            return self.title

        if self.request:
            return self.request.name

        return self.reference_code

    def __str__(self):
        return f"{self.reference_code} - {self.display_title}"


class ScheduleCalendar(BookingRequest):
    class Meta:
        proxy = True
        verbose_name = "Admin Calendar"
        verbose_name_plural = "Admin Calendar"