from django.test import TestCase

from .models import StudioService


class StudioSlugTests(TestCase):
    def test_service_slug_is_generated_and_unique(self):
        service_one = StudioService.objects.create(
            name="Mix Session",
        )
        service_two = StudioService.objects.create(
            name="Mix-Session",
        )

        self.assertTrue(service_one.slug)
        self.assertTrue(service_two.slug)
        self.assertNotEqual(service_one.slug, service_two.slug)