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

    def test_artist_list_shows_all_active_artists_alphabetically(self):
        active_featured = self.create_artist(name="Beta Featured Artist")
        active_non_featured = self.create_artist(
            name="Alpha Non Featured Artist",
            is_active=True,
            is_featured=False,
        )
        inactive = self.create_artist(
            name="Inactive Featured Artist",
            is_active=False,
        )

        response = self.client.get(reverse("artists:artist_list"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, active_featured.name)
        self.assertContains(response, active_non_featured.name)
        self.assertNotContains(response, inactive.name)

        content = response.content.decode()
        self.assertLess(
            content.index(active_non_featured.name),
            content.index(active_featured.name),
        )

    def test_artist_search_filters_active_artists(self):
        matching = self.create_artist(name="Searchable Band")
        other = self.create_artist(name="Other Band")
        non_featured_matching = self.create_artist(
            name="Searchable Non Featured Artist",
            is_active=True,
            is_featured=False,
        )
        inactive_matching = self.create_artist(
            name="Searchable Inactive Artist",
            is_active=False,
        )

        response = self.client.get(
            reverse("artists:artist_list"),
            {"q": "Searchable"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, matching.name)
        self.assertContains(response, non_featured_matching.name)
        self.assertNotContains(response, other.name)
        self.assertNotContains(response, inactive_matching.name)

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