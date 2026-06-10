from django.test import TestCase
from django.urls import reverse

from .models import NewsPost


class NewsPerformanceTests(TestCase):
    def create_post(
        self,
        title,
        status=NewsPost.Status.PUBLISHED,
        is_featured=False,
    ):
        return NewsPost.objects.create(
            title=title,
            summary="Summary",
            body="Body",
            status=status,
            is_featured=is_featured,
        )

    def test_news_list_does_not_duplicate_featured_post_lookup_excessively(self):
        self.create_post("Featured Post", is_featured=True)

        for index in range(12):
            self.create_post(f"Regular Post {index}")

        with self.assertNumQueries(4):
            response = self.client.get(reverse("news:news_list"))

        self.assertEqual(response.status_code, 200)