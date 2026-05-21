from django.test import TestCase
from django.urls import reverse

from .models import Artist
from .selectors import get_featured_artists


class ArtistQuerySetTests(TestCase):
    def setUp(self):
        # Create active featured artist
        self.featured_active = Artist.objects.create(
            name="Featured Active",
            slug="featured-active",
            is_featured=True,
            is_active=True,
        )
        # Create inactive featured artist
        self.featured_inactive = Artist.objects.create(
            name="Featured Inactive",
            slug="featured-inactive",
            is_featured=True,
            is_active=False,
        )
        # Create active non-featured artist
        self.nonfeatured_active = Artist.objects.create(
            name="Active Non-Featured",
            slug="active-nonfeatured",
            is_featured=False,
            is_active=True,
        )

    def test_active_filter(self):
        """Test .active() returns only active artists."""
        actives = Artist.objects.active()
        self.assertEqual(actives.count(), 2)
        self.assertIn(self.featured_active, actives)
        self.assertIn(self.nonfeatured_active, actives)
        self.assertNotIn(self.featured_inactive, actives)

    def test_featured_filter(self):
        """Test .featured() returns only active featured artists."""
        featureds = Artist.objects.featured()
        self.assertEqual(featureds.count(), 1)
        self.assertIn(self.featured_active, featureds)
        self.assertNotIn(self.featured_inactive, featureds)
        self.assertNotIn(self.nonfeatured_active, featureds)

    def test_get_featured_artists_selector(self):
        """Test get_featured_artists selector with and without limit."""
        # Create additional featured artists for limit test
        for i in range(3):
            Artist.objects.create(
                name=f"Featured {i}",
                slug=f"featured-{i}",
                is_featured=True,
                is_active=True,
                feature_order=i,
            )

        # Test without limit
        all_featured = get_featured_artists()
        self.assertEqual(all_featured.count(), 4)  # 1 from setUp + 3 new

        # Test with limit
        limited_featured = get_featured_artists(limit=2)
        self.assertEqual(limited_featured.count(), 2)

    def test_slug_is_generated_and_unique(self):
        """Artists should get a slug automatically and avoid duplicates."""
        first = Artist.objects.create(name="No Slug Artist")
        second = Artist.objects.create(name="No Slug Artist")

        self.assertTrue(first.slug)
        self.assertTrue(second.slug)
        self.assertNotEqual(first.slug, second.slug)


class ArtistViewsTests(TestCase):
    def setUp(self):
        self.artist = Artist.objects.create(
            name="Velvet Echo",
            slug="velvet-echo",
            short_bio="Neo-soul and indie grooves",
            is_featured=True,
            is_active=True,
        )

    def test_artist_list_loads(self):
        response = self.client.get(reverse("artists:artist_list"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Velvet Echo")

    def test_artist_search_filters_results(self):
        response = self.client.get(reverse("artists:artist_list"), {"q": "Velvet"})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Velvet Echo")

        response = self.client.get(reverse("artists:artist_list"), {"q": "NoMatch"})
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "Velvet Echo")