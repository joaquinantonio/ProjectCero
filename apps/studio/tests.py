from django.test import TestCase

from .models import StudioService, StudioServiceCategory


class StudioSlugTests(TestCase):
	def test_slug_is_generated_and_unique(self):
		"""Studio categories and services should get slugs automatically."""
		category_one = StudioServiceCategory.objects.create(name="Studio Category")
		category_two = StudioServiceCategory.objects.create(name="Studio-Category")

		self.assertTrue(category_one.slug)
		self.assertTrue(category_two.slug)
		self.assertNotEqual(category_one.slug, category_two.slug)

		service_one = StudioService.objects.create(
			category=category_one,
			name="Mix Session",
		)
		service_two = StudioService.objects.create(
			category=category_one,
			name="Mix-Session",
		)

		self.assertTrue(service_one.slug)
		self.assertTrue(service_two.slug)
		self.assertNotEqual(service_one.slug, service_two.slug)
