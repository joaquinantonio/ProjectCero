from datetime import timedelta
from decimal import Decimal

from django.db import connection
from django.test import TestCase
from django.test.utils import CaptureQueriesContext
from django.urls import reverse
from django.utils import timezone

from apps.artists.models import Artist
from apps.events.models import Event, EventArtist, EventCategory, TicketType
from apps.merch.models import MerchItem
from apps.news.models import NewsPost
from apps.pages.models import PageSection
from apps.studio.models import StudioService


class PublicQueryPerformanceTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.now = timezone.now()

        cls.category = EventCategory.objects.create(
            name="Performance Music",
            is_active=True,
        )

        cls.artists = []
        for index in range(6):
            artist = Artist.objects.create(
                name=f"Performance Artist {index}",
                short_bio="Short artist bio",
                bio="Long artist bio",
                artist_type=Artist.ArtistType.BAND,
                is_active=True,
                is_featured=True,
                feature_order=index,
            )
            cls.artists.append(artist)

        cls.events = []
        for index in range(12):
            event = Event.objects.create(
                category=cls.category,
                title=f"Performance Event {index}",
                short_description="Short event description",
                description="Long event description",
                start_at=cls.now + timedelta(days=index + 1),
                end_at=cls.now + timedelta(days=index + 1, hours=2),
                location_text="CeroPJ",
                status=Event.Status.PUBLISHED,
                is_featured=index < 4,
            )

            EventArtist.objects.create(
                event=event,
                artist=cls.artists[index % len(cls.artists)],
                role_name="Performer",
                sort_order=0,
            )

            cls.events.append(event)

        cls.event = cls.events[0]

        TicketType.objects.create(
            event=cls.event,
            name="General Admission",
            price_amount=Decimal("30.00"),
            currency="MYR",
            quantity_total=50,
            quantity_sold=5,
            is_active=True,
        )

        cls.merch_items = []
        for index in range(12):
            item = MerchItem.objects.create(
                name=f"Performance Merch {index}",
                short_description="Short merch description",
                description="Long merch description",
                price_amount=Decimal("50.00"),
                currency="MYR",
                is_active=True,
                is_featured=index < 4,
                track_stock=True,
                stock_quantity=10,
                display_order=index,
            )
            cls.merch_items.append(item)

        cls.merch_item = cls.merch_items[0]

        cls.news_posts = []
        for index in range(12):
            post = NewsPost.objects.create(
                title=f"Performance News {index}",
                summary="Short news summary",
                body="Long news body",
                status=NewsPost.Status.PUBLISHED,
                is_featured=index == 0,
            )
            cls.news_posts.append(post)

        cls.news_post = cls.news_posts[0]

        cls.studio_services = []
        for index in range(12):
            service = StudioService.objects.create(
                name=f"Performance Studio Service {index}",
                short_description="Short studio description",
                description="Long studio description",
                price_text="From RM100",
                duration_text="1 hour",
                is_active=True,
                is_featured=index < 4,
                display_order=index,
            )
            cls.studio_services.append(service)

        cls.studio_service = cls.studio_services[0]

        PageSection.objects.create(
            page_key=PageSection.PageKey.HOME,
            section_key="hero",
            title="Home Hero",
            body="Home hero content",
            is_active=True,
            sort_order=0,
        )

        PageSection.objects.create(
            page_key=PageSection.PageKey.ABOUT,
            section_key="intro",
            title="About Intro",
            body="About content",
            is_active=True,
            sort_order=0,
        )

        PageSection.objects.create(
            page_key=PageSection.PageKey.CONTACT,
            section_key="intro",
            title="Contact Intro",
            body="Contact content",
            is_active=True,
            sort_order=0,
        )

    def assert_max_queries(self, url, max_queries):
        with CaptureQueriesContext(connection) as captured:
            response = self.client.get(url)

        query_count = len(captured.captured_queries)

        debug_sql = "\n\n".join(
            query["sql"] for query in captured.captured_queries
        )

        self.assertEqual(response.status_code, 200)
        self.assertLessEqual(
            query_count,
            max_queries,
            msg=(
                f"{url} used {query_count} queries, expected max {max_queries}.\n\n"
                f"Queries:\n{debug_sql}"
            ),
        )

        return response

    def test_home_page_query_count_stays_reasonable(self):
        self.assert_max_queries(
            reverse("pages:home"),
            max_queries=14,
        )

    def test_event_list_query_count_stays_reasonable(self):
        self.assert_max_queries(
            reverse("events:event_list"),
            max_queries=10,
        )

    def test_event_detail_query_count_stays_reasonable(self):
        self.assert_max_queries(
            reverse("events:event_detail", args=[self.event.slug]),
            max_queries=9,
        )

    def test_artist_list_query_count_stays_reasonable(self):
        self.assert_max_queries(
            reverse("artists:artist_list"),
            max_queries=5,
        )

    def test_artist_detail_query_count_stays_reasonable(self):
        self.assert_max_queries(
            reverse("artists:artist_detail", args=[self.artists[0].slug]),
            max_queries=10,
        )

    def test_merch_list_query_count_stays_reasonable(self):
        self.assert_max_queries(
            reverse("merch:merch_list"),
            max_queries=6,
        )

    def test_merch_detail_query_count_stays_reasonable(self):
        self.assert_max_queries(
            reverse("merch:merch_detail", args=[self.merch_item.slug]),
            max_queries=5,
        )

    def test_news_list_query_count_stays_reasonable(self):
        self.assert_max_queries(
            reverse("news:news_list"),
            max_queries=5,
        )

    def test_news_detail_query_count_stays_reasonable(self):
        self.assert_max_queries(
            reverse("news:news_detail", args=[self.news_post.slug]),
            max_queries=5,
        )

    def test_studio_home_query_count_stays_reasonable(self):
        self.assert_max_queries(
            reverse("studio:home"),
            max_queries=5,
        )

    def test_studio_detail_query_count_stays_reasonable(self):
        self.assert_max_queries(
            reverse("studio:service_detail", args=[self.studio_service.slug]),
            max_queries=4,
        )