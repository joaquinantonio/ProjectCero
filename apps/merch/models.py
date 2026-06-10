from django.core.validators import MinValueValidator
from django.db import models

from apps.core.models import TimeStampedModel
from apps.core.utils import generate_unique_slug


class MerchItem(TimeStampedModel):
    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=220, unique=True)
    short_description = models.CharField(max_length=255, blank=True)
    description = models.TextField(blank=True)
    image = models.ImageField(upload_to="merch/items/", blank=True, null=True)

    price_text = models.CharField(max_length=100, blank=True)
    price_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0)],
        help_text="Numeric price used for future checkout calculations.",
    )
    currency = models.CharField(max_length=3, default="MYR")

    availability_text = models.CharField(
        max_length=120,
        blank=True,
        help_text="Optional text like 'Limited stock', 'Pre-order', or 'Sold out'.",
    )
    track_stock = models.BooleanField(
        default=False,
        help_text="Enable if stock quantity should be tracked.",
    )
    stock_quantity = models.PositiveIntegerField(
        default=0,
        help_text="Current available stock when stock tracking is enabled.",
    )

    cta_text = models.CharField(max_length=50, blank=True)
    cta_url = models.URLField(blank=True)

    is_featured = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    display_order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["display_order", "name"]
        indexes = [
            models.Index(fields=["is_active", "display_order"]),
            models.Index(fields=["is_featured", "display_order"]),
            models.Index(fields=["currency", "price_amount"]),
        ]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(price_amount__gte=0),
                name="merch_price_amount_non_negative",
            ),
        ]
        verbose_name = "Merchandise"
        verbose_name_plural = "Merchandise"

    def __str__(self):
        return self.name

    @property
    def is_in_stock(self):
        if not self.track_stock:
            return True
        return self.stock_quantity > 0

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = generate_unique_slug(self, self.name, max_length=220)

            update_fields = kwargs.get("update_fields")
            if update_fields is not None:
                kwargs["update_fields"] = set(update_fields) | {"slug"}

        super().save(*args, **kwargs)