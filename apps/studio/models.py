from django.db import models

from apps.core.models import SluggedModelMixin, TimeStampedModel
from apps.core.querysets import FeaturedQuerySet


class StudioServiceQuerySet(FeaturedQuerySet):
    pass


class StudioService(SluggedModelMixin, TimeStampedModel):
    objects = StudioServiceQuerySet.as_manager()

    slug_max_length = 170

    name = models.CharField(max_length=150)
    slug = models.SlugField(max_length=170, unique=True)
    short_description = models.CharField(max_length=255, blank=True)
    description = models.TextField(blank=True)
    image = models.ImageField(upload_to="studio/services/", blank=True, null=True)
    price_text = models.CharField(max_length=100, blank=True)
    duration_text = models.CharField(max_length=100, blank=True)
    is_featured = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    display_order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["display_order", "name"]
        indexes = [
            models.Index(fields=["is_active", "display_order"]),
            models.Index(fields=["is_featured", "display_order"]),
        ]

    def __str__(self):
        return self.name


class Equipment(TimeStampedModel):
    """Studio equipment list."""

    name = models.CharField(max_length=150)
    category = models.CharField(max_length=100, blank=True)
    description = models.TextField(blank=True)
    quantity = models.PositiveIntegerField(default=1)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["name"]
        indexes = [
            models.Index(fields=["is_active", "name"]),
        ]
        verbose_name_plural = "Equipment"

    def __str__(self):
        return self.name
