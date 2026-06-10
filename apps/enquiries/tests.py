from datetime import timedelta

from django.core import mail
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from apps.events.models import Event, EventCategory
from apps.merch.models import MerchItem

from .models import EnquirySubmission


@override_settings(
    EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
    ENQUIRY_NOTIFICATION_EMAIL="enquiries@example.com",
    DEFAULT_FROM_EMAIL="CeroPJ <no-reply@example.com>",
)
class EnquiryFlowTests(TestCase):
    def create_event(self):
        category = EventCategory.objects.create(
            name="Music",
            is_active=True,
        )

        return Event.objects.create(
            category=category,
            title="Payment Event",
            start_at=timezone.now() + timedelta(days=7),
            status=Event.Status.PUBLISHED,
        )

    def create_merch_item(self):
        return MerchItem.objects.create(
            name="Cero Tee",
            price_amount="50.00",
            currency="MYR",
            is_active=True,
        )

    def test_general_enquiry_creates_reference_and_sends_email(self):
        response = self.client.post(
            reverse("enquiries:general"),
            {
                "name": "General User",
                "email": "general@example.com",
                "phone": "0123456789",
                "subject": "General question",
                "preferred_date": "2026-06-15",
                "message": "I have a general question.",
            },
        )

        self.assertRedirects(response, reverse("enquiries:success"))
        self.assertEqual(EnquirySubmission.objects.count(), 1)

        enquiry = EnquirySubmission.objects.first()
        self.assertTrue(enquiry.reference_code.startswith("ENQ-"))
        self.assertEqual(enquiry.enquiry_type, EnquirySubmission.EnquiryType.GENERAL)

        self.assertEqual(len(mail.outbox), 1)
        self.assertIn(enquiry.reference_code, mail.outbox[0].subject)

    def test_honeypot_blocks_enquiry_submission(self):
        response = self.client.post(
            reverse("enquiries:general"),
            {
                "name": "Spam Bot",
                "email": "spam@example.com",
                "phone": "0000000000",
                "subject": "Spam",
                "message": "Spam message",
                "website": "http://spam.example.com",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(EnquirySubmission.objects.count(), 0)
        self.assertEqual(len(mail.outbox), 0)

    def test_merch_enquiry_prefills_related_merch_from_query_string(self):
        item = self.create_merch_item()

        response = self.client.get(
            reverse("enquiries:merch"),
            {"item": item.slug},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["form"].initial["related_merch"], item.pk)

    def test_general_enquiry_prefills_related_event_from_query_string(self):
        event = self.create_event()

        response = self.client.get(
            reverse("enquiries:general"),
            {"event": event.slug},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["form"].initial["related_event"], event.pk)
        self.assertEqual(
            response.context["form"].initial["subject"],
            f"General enquiry: {event.title}",
        )

    def test_studio_enquiry_creates_studio_submission(self):
        response = self.client.post(
            reverse("enquiries:studio"),
            {
                "name": "Studio User",
                "email": "studio@example.com",
                "phone": "0123456789",
                "subject": "Studio question",
                "preferred_date": "2026-06-15",
                "preferred_start_time": "13:00",
                "message": "I want to ask about studio services.",
            },
        )

        self.assertRedirects(response, reverse("enquiries:success"))

        enquiry = EnquirySubmission.objects.get()
        self.assertEqual(enquiry.enquiry_type, EnquirySubmission.EnquiryType.STUDIO)
        self.assertEqual(enquiry.subject, "Studio question")

    def test_venue_enquiry_creates_venue_submission(self):
        response = self.client.post(
            reverse("enquiries:venue"),
            {
                "name": "Venue User",
                "email": "venue@example.com",
                "phone": "0123456789",
                "subject": "Venue question",
                "preferred_date": "2026-06-15",
                "preferred_start_time": "15:00",
                "message": "I want to ask about venue facilities.",
            },
        )

        self.assertRedirects(response, reverse("enquiries:success"))

        enquiry = EnquirySubmission.objects.get()
        self.assertEqual(enquiry.enquiry_type, EnquirySubmission.EnquiryType.VENUE)
        self.assertEqual(enquiry.subject, "Venue question")

    def test_merch_enquiry_creates_merch_submission_with_quantity(self):
        item = self.create_merch_item()

        response = self.client.post(
            reverse("enquiries:merch"),
            {
                "name": "Merch User",
                "email": "merch@example.com",
                "phone": "0123456789",
                "related_merch": item.pk,
                "quantity": 2,
                "message": "I would like to purchase this item.",
            },
        )

        self.assertRedirects(response, reverse("enquiries:success"))

        enquiry = EnquirySubmission.objects.get()
        self.assertEqual(enquiry.enquiry_type, EnquirySubmission.EnquiryType.MERCH)
        self.assertEqual(enquiry.related_merch, item)
        self.assertEqual(enquiry.quantity, 2)
        self.assertIn("Merch purchase enquiry", enquiry.subject)