from django.db import models

from apps.core.models import SluggedModelMixin, TimeStampedModel
from apps.core.querysets import FeaturedQuerySet


class ArtistQuerySet(FeaturedQuerySet):
    pass


class Artist(SluggedModelMixin, TimeStampedModel):
    objects = ArtistQuerySet.as_manager()

    class ArtistType(models.TextChoices):
        SOLO = "solo", "Solo Artist"
        BAND = "band", "Band"
        DJ = "dj", "DJ"
        OTHER = "other", "Other"

    name = models.CharField(max_length=150)
    slug = models.SlugField(max_length=170, unique=True)
    short_bio = models.CharField(max_length=255, blank=True)
    bio = models.TextField(blank=True)
    image = models.ImageField(upload_to="artists/", blank=True, null=True)

    instagram_url = models.URLField(max_length=500, blank=True)
    spotify_url = models.URLField(max_length=500, blank=True)
    youtube_url = models.URLField(max_length=500, blank=True)

    artist_type = models.CharField(
        max_length=20,
        choices=ArtistType,
        default=ArtistType.BAND,
    )
    is_featured = models.BooleanField(default=False)
    feature_order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["feature_order", "name"]
        indexes = [
            models.Index(fields=["is_active", "name"]),
            models.Index(fields=["is_featured", "feature_order"]),
        ]

    def __str__(self):
        return self.name