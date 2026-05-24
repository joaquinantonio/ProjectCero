from django.test import TestCase
from django.urls import reverse

from .models import NewsPost


class NewsPublicTests(TestCase):
    def create_post(
        self,
        title="News Post",
        status=NewsPost.Status.PUBLISHED,
        is_featured=False,
    ):
        return NewsPost.objects.create(
            title=title,
            summary="Short summary",
            body="Long news body",
            status=status,
            is_featured=is_featured,
        )

    def test_published_news_sets_slug_and_published_at(self):
        post = self.create_post(title="New Announcement")

        self.assertTrue(post.slug)
        self.assertIsNotNone(post.published_at)

    def test_news_list_only_shows_published_posts(self):
        published = self.create_post(title="Published News")
        draft = self.create_post(title="Draft News", status=NewsPost.Status.DRAFT)

        response = self.client.get(reverse("news:news_list"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, published.title)
        self.assertNotContains(response, draft.title)

    def test_featured_post_is_exposed_in_context(self):
        featured = self.create_post(
            title="Featured News",
            status=NewsPost.Status.PUBLISHED,
            is_featured=True,
        )

        response = self.client.get(reverse("news:news_list"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["featured_post"], featured)

    def test_published_detail_loads_but_draft_detail_is_404(self):
        published = self.create_post(title="Published Detail")
        draft = self.create_post(title="Draft Detail", status=NewsPost.Status.DRAFT)

        response = self.client.get(
            reverse("news:news_detail", args=[published.slug])
        )
        self.assertEqual(response.status_code, 200)

        response = self.client.get(
            reverse("news:news_detail", args=[draft.slug])
        )
        self.assertEqual(response.status_code, 404)