from django.core import mail
from django.test import TestCase, override_settings
from django.urls import reverse

from .models import BookingRequest


@override_settings(
    EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
    BOOKING_NOTIFICATION_EMAIL="notify@example.com",
    DEFAULT_FROM_EMAIL="no-reply@example.com",
)
class BookingRequestTests(TestCase):
    def test_general_booking_creates_record_and_sends_email(self):
        response = self.client.post(
            reverse("bookings:general_request"),
            {
                "name": "Test User",
                "email": "test@example.com",
                "phone": "0123456789",
                "message": "Hello there",
            },
        )

        self.assertRedirects(response, reverse("bookings:success"))
        self.assertEqual(BookingRequest.objects.count(), 1)
        self.assertEqual(len(mail.outbox), 2)
        # First email is admin notification
        self.assertIn("General", mail.outbox[0].subject)
        # Second email is user confirmation
        self.assertEqual(mail.outbox[1].to, ["test@example.com"])

    def test_invalid_venue_booking_does_not_submit(self):
        response = self.client.post(
            reverse("bookings:venue_request"),
            {
                "name": "CeroPJ User",
                "email": "venue@example.com",
                "phone": "0123456789",
                "message": "Need the venue",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(BookingRequest.objects.count(), 0)
        self.assertEqual(len(mail.outbox), 0)

    def test_honeypot_blocks_submission(self):
        response = self.client.post(
            reverse("bookings:general_request"),
            {
                "name": "Spam Bot",
                "email": "spam@example.com",
                "phone": "0000000000",
                "message": "Spam message",
                "website": "http://spam.example.com",
            },
        )

        self.assertRedirects(response, reverse("bookings:success"))
        self.assertEqual(BookingRequest.objects.count(), 0)