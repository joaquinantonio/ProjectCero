from django.test import TestCase
from django.urls import reverse

from .models import Artist


class ArtistPublicTests(TestCase):
    def create_artist(
        self,
        name="Cero Test Band",
        is_active=True,
        is_featured=True,
    ):
        return Artist.objects.create(
            name=name,
            short_bio="Short bio",
            bio="Long bio",
            artist_type=Artist.ArtistType.BAND,
            is_active=is_active,
            is_featured=is_featured,
        )

    def test_artist_slug_is_generated_and_unique(self):
        artist_one = self.create_artist(name="Cero Test Band")
        artist_two = self.create_artist(name="Cero-Test-Band")

        self.assertTrue(artist_one.slug)
        self.assertTrue(artist_two.slug)
        self.assertNotEqual(artist_one.slug, artist_two.slug)

    def test_artist_list_shows_featured_active_artists_only(self):
        active = self.create_artist(name="Active Featured Artist")
        inactive = self.create_artist(name="Inactive Featured Artist", is_active=False)
        non_featured = self.create_artist(
            name="Active Non Featured Artist",
            is_active=True,
            is_featured=False,
        )

        response = self.client.get(reverse("artists:artist_list"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, active.name)
        self.assertNotContains(response, inactive.name)
        self.assertNotContains(response, non_featured.name)

    def test_artist_search_filters_featured_artists(self):
        matching = self.create_artist(name="Searchable Band")
        other = self.create_artist(name="Other Band")

        response = self.client.get(
            reverse("artists:artist_list"),
            {"q": "Searchable"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, matching.name)
        self.assertNotContains(response, other.name)

    def test_active_artist_detail_loads_but_inactive_detail_is_404(self):
        active = self.create_artist(name="Active Artist")
        inactive = self.create_artist(name="Inactive Artist", is_active=False)

        response = self.client.get(
            reverse("artists:artist_detail", args=[active.slug])
        )
        self.assertEqual(response.status_code, 200)

        response = self.client.get(
            reverse("artists:artist_detail", args=[inactive.slug])
        )
        self.assertEqual(response.status_code, 404)