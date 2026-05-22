from django.db import models
from django.utils import timezone

from apps.core.models import TimeStampedModel
from apps.core.utils import generate_unique_slug


class NewsPost(TimeStampedModel):
    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        PUBLISHED = "published", "Published"

    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=220, unique=True)
    summary = models.CharField(max_length=255, blank=True)
    body = models.TextField()
    cover_image = models.ImageField(upload_to="news/covers/", blank=True, null=True)

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.DRAFT,
    )
    is_featured = models.BooleanField(default=False)
    published_at = models.DateTimeField(blank=True, null=True, editable=False)

    class Meta:
        ordering = ["-published_at", "-created_at", "title"]
        indexes = [
            models.Index(fields=["status", "-published_at"]),
            models.Index(fields=["is_featured", "-published_at"]),
        ]
        verbose_name = "News post"
        verbose_name_plural = "News"

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = generate_unique_slug(self, self.title, max_length=220)

            update_fields = kwargs.get("update_fields")
            if update_fields is not None:
                kwargs["update_fields"] = set(update_fields) | {"slug"}

        if self.status == self.Status.PUBLISHED and not self.published_at:
            self.published_at = timezone.now()

            update_fields = kwargs.get("update_fields")
            if update_fields is not None:
                kwargs["update_fields"] = set(update_fields) | {"published_at"}

        super().save(*args, **kwargs)