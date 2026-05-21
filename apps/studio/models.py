from django.db import models

from apps.core.models import SluggedModelMixin, TimeStampedModel
from apps.core.querysets import ActiveQuerySet, FeaturedQuerySet


class StudioServiceCategoryQuerySet(ActiveQuerySet):
    pass


class StudioServiceCategory(SluggedModelMixin, TimeStampedModel):
    objects = StudioServiceCategoryQuerySet.as_manager()

    slug_max_length = 120

    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=120, unique=True)
    sort_order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["sort_order", "name"]
        verbose_name = "Studio category"
        verbose_name_plural = "Studio categories"
        indexes = [
            models.Index(fields=["is_active", "sort_order"]),
        ]

    def __str__(self):
        return self.name


class StudioServiceQuerySet(FeaturedQuerySet):
    pass


class StudioService(SluggedModelMixin, TimeStampedModel):
    objects = StudioServiceQuerySet.as_manager()

    slug_max_length = 170

    category = models.ForeignKey(
        StudioServiceCategory,
        on_delete=models.PROTECT,
        related_name="services",
    )
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
            models.Index(fields=["category", "display_order"]),
        ]

    def __str__(self):
        return self.name