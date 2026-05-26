from uuid import uuid4

from django.db import models

from apps.core.models import TimeStampedModel


class EnquirySubmission(TimeStampedModel):
    class EnquiryType(models.TextChoices):
        GENERAL = "general", "General"
        MERCH = "merch", "Merch"
        PAYMENT = "payment", "Payment"
        STUDIO = "studio", "Studio"
        VENUE = "venue", "Venue"

    class Status(models.TextChoices):
        NEW = "new", "New"
        IN_REVIEW = "in_review", "In Review"
        REPLIED = "replied", "Replied"
        CLOSED = "closed", "Closed"

    reference_code = models.CharField(max_length=20, unique=True, editable=False)
    enquiry_type = models.CharField(max_length=20, choices=EnquiryType.choices)

    name = models.CharField(max_length=150)
    email = models.EmailField()
    phone = models.CharField(max_length=50, blank=True)

    subject = models.CharField(max_length=200)
    preferred_date = models.DateField(blank=True, null=True)
    preferred_start_time = models.TimeField(blank=True, null=True)

    related_event = models.ForeignKey(
        "events.Event",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="enquiry_submissions",
    )
    related_merch = models.ForeignKey(
        "merch.MerchItem",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="enquiry_submissions",
    )

    amount_text = models.CharField(max_length=100, blank=True)
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
            models.Index(fields=["enquiry_type", "status"]),
            models.Index(fields=["status", "created_at"]),
        ]
        verbose_name = "Enquiry submission"
        verbose_name_plural = "Enquiries"

    def __str__(self):
        return f"{self.reference_code} - {self.name}"

    def save(self, *args, **kwargs):
        if not self.reference_code:
            while True:
                code = f"ENQ-{uuid4().hex[:8].upper()}"
                if not EnquirySubmission.objects.filter(reference_code=code).exists():
                    self.reference_code = code
                    break

            update_fields = kwargs.get("update_fields")
            if update_fields is not None:
                kwargs["update_fields"] = set(update_fields) | {"reference_code"}

        super().save(*args, **kwargs)


class ArtistEnquiry(TimeStampedModel):
    """Contact form for enquiring about artists."""

    class Status(models.TextChoices):
        NEW = "new", "New"
        CONTACTED = "contacted", "Contacted"
        CLOSED = "closed", "Closed"

    reference_code = models.CharField(max_length=20, unique=True, editable=False)

    name = models.CharField(max_length=150)
    email = models.EmailField()
    phone = models.CharField(max_length=50)

    related_artist = models.ForeignKey(
        "artists.Artist",
        on_delete=models.CASCADE,
        related_name="enquiries",
    )

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
            models.Index(fields=["related_artist", "status"]),
        ]
        verbose_name = "Artist enquiry"
        verbose_name_plural = "Artist enquiries"

    def __str__(self):
        return f"{self.reference_code} - {self.name} ({self.related_artist.name})"


    def save(self, *args, **kwargs):
        if not self.reference_code:
            while True:
                code = f"ARTQ-{uuid4().hex[:8].upper()}"
                if not ArtistEnquiry.objects.filter(reference_code=code).exists():
                    self.reference_code = code
                    break

            update_fields = kwargs.get("update_fields")
            if update_fields is not None:
                kwargs["update_fields"] = set(update_fields) | {"reference_code"}

        super().save(*args, **kwargs)
