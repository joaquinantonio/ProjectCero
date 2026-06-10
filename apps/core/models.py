from django.db import models

from apps.core.utils import generate_unique_slug


class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class SluggedModelMixin(models.Model):
    slug_source_field = "name"
    slug_field = "slug"
    slug_max_length = 170

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        slug_value = getattr(self, self.slug_field, None)
        if not slug_value:
            source_value = getattr(self, self.slug_source_field, "")
            setattr(
                self,
                self.slug_field,
                generate_unique_slug(
                    self,
                    source_value,
                    slug_field=self.slug_field,
                    max_length=self.slug_max_length,
                ),
            )

            update_fields = kwargs.get("update_fields")
            if update_fields is not None:
                kwargs["update_fields"] = [*update_fields, self.slug_field]

        super().save(*args, **kwargs)
