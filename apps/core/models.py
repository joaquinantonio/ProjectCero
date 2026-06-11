from uuid import uuid4

from django.db import models

from apps.core.utils import generate_unique_slug


class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class ReferenceCodeMixin(models.Model):
    reference_code_prefix = None
    reference_code_random_length = 8
    reference_code_field = "reference_code"

    class Meta:
        abstract = True

    def generate_reference_code(self):
        if not self.reference_code_prefix:
            raise ValueError(
                f"{self.__class__.__name__} must define reference_code_prefix."
            )

        model_class = self.__class__
        field_name = self.reference_code_field

        while True:
            reference_code = (
                f"{self.reference_code_prefix}-"
                f"{uuid4().hex[: self.reference_code_random_length].upper()}"
            )

            exists = (
                model_class._default_manager.filter(**{field_name: reference_code})
                .exclude(pk=self.pk)
                .exists()
            )

            if not exists:
                return reference_code

    def save(self, *args, **kwargs):
        field_name = self.reference_code_field

        if not getattr(self, field_name):
            setattr(self, field_name, self.generate_reference_code())

            update_fields = kwargs.get("update_fields")
            if update_fields is not None:
                kwargs["update_fields"] = set(update_fields) | {field_name}

        super().save(*args, **kwargs)


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