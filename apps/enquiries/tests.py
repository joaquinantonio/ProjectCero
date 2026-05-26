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

    def test_general_enquiry_prefills_related_merch_from_query_string(self):
        item = self.create_merch_item()

        response = self.client.get(
            reverse("enquiries:general"),
            {"item": item.slug},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["form"].initial["related_merch"], item.pk)
        self.assertEqual(
            response.context["form"].initial["subject"],
            f"General enquiry: {item.name}",
        )

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

    def test_general_enquiry_can_capture_amount_context(self):
        event = self.create_event()

        response = self.client.post(
            reverse("enquiries:general"),
            {
                "name": "Payment User",
                "email": "payment@example.com",
                "phone": "0123456789",
                "subject": "Payment question",
                "related_event": event.pk,
                "amount_text": "RM100",
                "message": "I want to ask about payment follow-up.",
            },
        )

        self.assertRedirects(response, reverse("enquiries:success"))

        enquiry = EnquirySubmission.objects.get()
        self.assertEqual(enquiry.enquiry_type, EnquirySubmission.EnquiryType.GENERAL)
        self.assertEqual(enquiry.related_event, event)
        self.assertEqual(enquiry.amount_text, "RM100")