from django.core.exceptions import ValidationError
from django.db import models

from apps.core.models import TimeStampedModel
from apps.core.querysets import ActiveQuerySet


class SiteSettings(TimeStampedModel):
    site_name = models.CharField(max_length=150)
    tagline = models.CharField(max_length=255, blank=True)
    contact_email = models.EmailField()
    contact_phone = models.CharField(max_length=50, blank=True)
    address_text = models.TextField(blank=True)
    google_maps_url = models.URLField(max_length=500, blank=True)
    instagram_url = models.URLField(max_length=500, blank=True)
    facebook_url = models.URLField(max_length=500, blank=True)
    tiktok_url = models.URLField(max_length=500, blank=True)
    youtube_url = models.URLField(max_length=500, blank=True)
    whatsapp_url = models.URLField(max_length=500, blank=True)

    class Meta:
        verbose_name = "Site settings"
        verbose_name_plural = "Site settings"

    def clean(self):
        if not self.pk and SiteSettings.objects.exists():
            raise ValidationError("Only one SiteSettings record is allowed.")

    def save(self, *args, **kwargs):
        if not self.pk:
            self.pk = 1
        super().save(*args, **kwargs)

    def __str__(self):
        return self.site_name


class PageSectionQuerySet(ActiveQuerySet):
    def for_page(self, page_key):
        return self.filter(page_key=page_key)

    def for_page_active(self, page_key):
        return self.for_page(page_key).active()


class PageSection(TimeStampedModel):
    objects = PageSectionQuerySet.as_manager()

    class PageKey(models.TextChoices):
        HOME = "home", "Home"
        ABOUT = "about", "About"
        CONTACT = "contact", "Contact"
        STUDIO = "studio", "Studio"
        EVENTS = "events", "Events"

    page_key = models.CharField(max_length=20, choices=PageKey)
    section_key = models.SlugField(max_length=50)
    title = models.CharField(max_length=200, blank=True)
    subtitle = models.CharField(max_length=255, blank=True)
    body = models.TextField(blank=True)
    image = models.ImageField(upload_to="pages/sections/", blank=True, null=True)
    cta_text = models.CharField(max_length=100, blank=True)
    cta_url = models.URLField(max_length=500, blank=True)
    sort_order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["page_key", "sort_order", "id"]
        constraints = [
            models.UniqueConstraint(
                fields=["page_key", "section_key"],
                name="unique_page_section_key",
            )
        ]
        indexes = [
            models.Index(fields=["page_key", "is_active", "sort_order"]),
        ]

    def __str__(self):
        return f"{self.page_key}:{self.section_key}"