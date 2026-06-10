from datetime import timedelta
from decimal import Decimal

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from .models import Event, EventCategory, TicketType


class EventPublicTests(TestCase):
    def create_category(self, name="Music"):
        category, _ = EventCategory.objects.get_or_create(
            name=name,
            defaults={
                "is_active": True,
            },
        )

        if not category.is_active:
            category.is_active = True
            category.save(update_fields=["is_active", "updated_at"])

        return category

    def create_event(
        self,
        title="Live Night",
        status=Event.Status.PUBLISHED,
        start_at=None,
        end_at=None,
        category=None,
    ):
        category = category or self.create_category()

        return Event.objects.create(
            category=category,
            title=title,
            short_description="Short description",
            description="Long description",
            start_at=start_at or timezone.now() + timedelta(days=7),
            end_at=end_at,
            location_text="CeroPJ",
            status=status,
        )

    def test_published_event_sets_slug_and_published_at(self):
        event = self.create_event(title="Friday Jam")

        self.assertTrue(event.slug)
        self.assertIsNotNone(event.published_at)

    def test_published_event_detail_is_public_but_draft_is_404(self):
        published = self.create_event(title="Public Event")
        draft = self.create_event(title="Draft Event", status=Event.Status.DRAFT)

        response = self.client.get(
            reverse("events:event_detail", args=[published.slug])
        )
        self.assertEqual(response.status_code, 200)

        response = self.client.get(
            reverse("events:event_detail", args=[draft.slug])
        )
        self.assertEqual(response.status_code, 404)

    def test_event_list_shows_published_upcoming_event(self):
        event = self.create_event(title="Upcoming Public Event")
        self.create_event(title="Hidden Draft Event", status=Event.Status.DRAFT)

        response = self.client.get(reverse("events:event_list"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, event.title)
        self.assertNotContains(response, "Hidden Draft Event")

    def test_event_calendar_feed_returns_published_events(self):
        event = self.create_event(title="Calendar Event")
        self.create_event(title="Draft Calendar Event", status=Event.Status.DRAFT)

        response = self.client.get(
            reverse("events:calendar_feed"),
            {
                "start": (timezone.now() - timedelta(days=1)).isoformat(),
                "end": (timezone.now() + timedelta(days=30)).isoformat(),
            },
        )

        self.assertEqual(response.status_code, 200)

        data = response.json()
        titles = [item["title"] for item in data]

        self.assertIn(event.title, titles)
        self.assertNotIn("Draft Calendar Event", titles)

    def test_event_detail_only_exposes_active_available_ticket_types(self):
        event = self.create_event(title="Ticketed Event")

        available_ticket = TicketType.objects.create(
            event=event,
            name="Early Bird",
            price_amount=Decimal("30.00"),
            currency="MYR",
            quantity_total=10,
            quantity_sold=2,
            is_active=True,
        )

        TicketType.objects.create(
            event=event,
            name="Sold Out",
            price_amount=Decimal("40.00"),
            currency="MYR",
            quantity_total=5,
            quantity_sold=5,
            is_active=True,
        )

        TicketType.objects.create(
            event=event,
            name="Inactive",
            price_amount=Decimal("50.00"),
            currency="MYR",
            quantity_total=5,
            quantity_sold=0,
            is_active=False,
        )

        response = self.client.get(
            reverse("events:event_detail", args=[event.slug])
        )

        self.assertEqual(response.status_code, 200)

        ticket_types = list(response.context["ticket_types"])
        self.assertIn(available_ticket, ticket_types)
        self.assertEqual(len(ticket_types), 1)

    def test_single_event_ics_feed_returns_calendar_file(self):
        event = self.create_event(title="ICS Event")

        response = self.client.get(
            reverse("events:single_event_ics", args=[event.slug])
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "text/calendar")
        self.assertIn(b"BEGIN:VCALENDAR", response.content)
        self.assertIn(b"ICS Event", response.content)