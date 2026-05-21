from django.db import models
from django.utils import timezone

from apps.artists.models import Artist
from apps.core.models import SluggedModelMixin, TimeStampedModel
from apps.core.querysets import ActiveQuerySet


class EventCategoryQuerySet(ActiveQuerySet):
    pass


class EventCategory(SluggedModelMixin, TimeStampedModel):
    objects = EventCategoryQuerySet.as_manager()

    slug_max_length = 120

    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=120, unique=True)
    description = models.TextField(blank=True)
    sort_order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["sort_order", "name"]
        verbose_name = "Event category"
        verbose_name_plural = "Event categories"
        indexes = [
            models.Index(fields=["is_active", "sort_order"]),
        ]

    def __str__(self):
        return self.name


class Event(SluggedModelMixin, TimeStampedModel):
    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        PUBLISHED = "published", "Published"
        CANCELLED = "cancelled", "Cancelled"

    category = models.ForeignKey(
        EventCategory,
        on_delete=models.PROTECT,
        related_name="events",
    )
    slug_source_field = "title"
    slug_max_length = 220
    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=220, unique=True)
    short_description = models.CharField(max_length=255, blank=True)
    description = models.TextField(blank=True)
    poster = models.ImageField(upload_to="events/posters/", blank=True, null=True)

    start_at = models.DateTimeField()
    end_at = models.DateTimeField(blank=True, null=True)
    time_note = models.CharField(
        max_length=120,
        blank=True,
        help_text="Optional public-facing timing text, e.g. '10 PM until late' or '8 PM onwards'.",
    )

    location_text = models.CharField(max_length=255, blank=True)
    ticket_url = models.URLField(blank=True)
    price_text = models.CharField(max_length=100, blank=True)

    status = models.CharField(
        max_length=20,
        choices=Status,
        default=Status.DRAFT,
    )
    is_featured = models.BooleanField(default=False)
    published_at = models.DateTimeField(blank=True, null=True, editable=False)

    class Meta:
        ordering = ["start_at", "title"]
        indexes = [
            models.Index(fields=["status", "start_at"]),
            models.Index(fields=["is_featured", "start_at"]),
            models.Index(fields=["category", "start_at"]),
        ]

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if self.status == self.Status.PUBLISHED and not self.published_at:
            self.published_at = timezone.now()

            update_fields = kwargs.get("update_fields")
            if update_fields is not None:
                kwargs["update_fields"] = [*update_fields, "published_at"]

        super().save(*args, **kwargs)

    @property
    def display_time_text(self):
        if self.time_note:
            return self.time_note

        start_text = timezone.localtime(self.start_at).strftime("%-I:%M %p") if self.start_at else ""
        if self.end_at:
            end_text = timezone.localtime(self.end_at).strftime("%-I:%M %p")
            return f"{start_text} – {end_text}"
        return start_text


class EventArtist(TimeStampedModel):
    event = models.ForeignKey(
        Event,
        on_delete=models.CASCADE,
        related_name="event_artists",
    )
    artist = models.ForeignKey(
        Artist,
        on_delete=models.PROTECT,
        related_name="event_links",
    )
    role_name = models.CharField(max_length=100, blank=True)
    sort_order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["sort_order", "id"]
        constraints = [
            models.UniqueConstraint(
                fields=["event", "artist"],
                name="unique_event_artist",
            ),
        ]
        indexes = [
            models.Index(fields=["event", "sort_order"]),
            models.Index(fields=["artist"]),
        ]

    def __str__(self):
        return f"{self.event} - {self.artist}"