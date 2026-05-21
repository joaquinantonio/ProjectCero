from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta

from apps.artists.models import Artist
from .models import Event, EventCategory, EventArtist
from .selectors import get_upcoming_events


class EventCategoryQuerySetTests(TestCase):
    def setUp(self):
        self.active_category = EventCategory.objects.create(
            name="Active Category",
            slug="active-category",
            is_active=True,
        )
        self.inactive_category = EventCategory.objects.create(
            name="Inactive Category",
            slug="inactive-category",
            is_active=False,
        )

    def test_active_filter(self):
        """Test .active() returns only active categories."""
        actives = EventCategory.objects.active()
        self.assertEqual(actives.count(), 1)
        self.assertIn(self.active_category, actives)
        self.assertNotIn(self.inactive_category, actives)

    def test_active_ordering(self):
        """Test active categories are ordered by sort_order and name."""
        cat1 = EventCategory.objects.create(
            name="ZZZ",
            slug="zzz",
            sort_order=2,
            is_active=True,
        )
        cat2 = EventCategory.objects.create(
            name="AAA",
            slug="aaa",
            sort_order=1,
            is_active=True,
        )
        actives = EventCategory.objects.active()
        # Should be ordered by sort_order, then name
        # self.active_category has sort_order=0 (default), cat2 has sort_order=1, cat1 has sort_order=2
        self.assertEqual(list(actives), [self.active_category, cat2, cat1])

    def test_slug_is_generated_and_unique(self):
        """Categories and events should get slugs automatically."""
        first_category = EventCategory.objects.create(name="Live Gig")
        second_category = EventCategory.objects.create(name="Live-Gig")

        self.assertTrue(first_category.slug)
        self.assertTrue(second_category.slug)
        self.assertNotEqual(first_category.slug, second_category.slug)

        event_one = Event.objects.create(
            category=first_category,
            title="Night Session",
            start_at=timezone.now() + timedelta(days=1),
        )
        event_two = Event.objects.create(
            category=first_category,
            title="Night-Session",
            start_at=timezone.now() + timedelta(days=2),
        )

        self.assertTrue(event_one.slug)
        self.assertTrue(event_two.slug)
        self.assertNotEqual(event_one.slug, event_two.slug)


class EventViewsTests(TestCase):
    def setUp(self):
        self.category = EventCategory.objects.create(
            name="Live Gig",
            slug="live-gig",
            is_active=True,
        )
        self.artist = Artist.objects.create(
            name="Test Band",
            slug="test-band",
            is_active=True,
            is_featured=True,
        )

        self.published_event = Event.objects.create(
            category=self.category,
            title="Published Event",
            slug="published-event",
            start_at=timezone.now() + timedelta(days=3),
            status=Event.Status.PUBLISHED,
        )
        EventArtist.objects.create(
            event=self.published_event,
            artist=self.artist,
            sort_order=1,
        )

        self.draft_event = Event.objects.create(
            category=self.category,
            title="Draft Event",
            slug="draft-event",
            start_at=timezone.now() + timedelta(days=5),
            status=Event.Status.DRAFT,
        )

    def test_event_list_shows_published_event_only(self):
        response = self.client.get(reverse("events:event_list"))
        self.assertContains(response, "Published Event")
        self.assertNotContains(response, "Draft Event")

    def test_artist_detail_page_loads(self):
        response = self.client.get(reverse("artists:artist_detail", args=[self.artist.slug]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Test Band")

    def test_calendar_feed_returns_published_event_only(self):
        response = self.client.get(reverse("events:calendar_feed"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Published Event")
        self.assertNotContains(response, "Draft Event")

    def test_event_search_filters_results(self):
        response = self.client.get(reverse("events:event_list"), {"q": "Published"})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Published Event")

        response = self.client.get(reverse("events:event_list"), {"q": "NoMatch"})
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "Published Event")