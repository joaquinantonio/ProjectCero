from decimal import Decimal

from django.test import TestCase
from django.urls import reverse

from .models import MerchItem


class MerchPublicTests(TestCase):
    def create_item(
        self,
        name="Cero Tee",
        is_active=True,
        is_featured=False,
        track_stock=True,
        stock_quantity=5,
    ):
        return MerchItem.objects.create(
            name=name,
            short_description="Short merch description",
            description="Long merch description",
            price_amount=Decimal("50.00"),
            currency="MYR",
            is_active=is_active,
            is_featured=is_featured,
            track_stock=track_stock,
            stock_quantity=stock_quantity,
        )

    def test_merch_slug_is_generated_and_unique(self):
        item_one = self.create_item(name="Cero Tee")
        item_two = self.create_item(name="Cero-Tee")

        self.assertTrue(item_one.slug)
        self.assertTrue(item_two.slug)
        self.assertNotEqual(item_one.slug, item_two.slug)

    def test_stock_property_respects_tracking(self):
        tracked_empty = self.create_item(
            name="Tracked Empty",
            track_stock=True,
            stock_quantity=0,
        )
        untracked_empty = self.create_item(
            name="Untracked Empty",
            track_stock=False,
            stock_quantity=0,
        )

        self.assertFalse(tracked_empty.is_in_stock)
        self.assertTrue(untracked_empty.is_in_stock)

    def test_merch_list_only_shows_active_items(self):
        active = self.create_item(name="Active Tee", is_active=True)
        inactive = self.create_item(name="Inactive Tee", is_active=False)

        response = self.client.get(reverse("merch:merch_list"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, active.name)
        self.assertNotContains(response, inactive.name)

    def test_inactive_merch_detail_is_404(self):
        inactive = self.create_item(name="Inactive Tee", is_active=False)

        response = self.client.get(
            reverse("merch:merch_detail", args=[inactive.slug])
        )

        self.assertEqual(response.status_code, 404)

    def test_active_merch_detail_loads(self):
        item = self.create_item(name="Active Tee", is_active=True)

        response = self.client.get(
            reverse("merch:merch_detail", args=[item.slug])
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, item.name)