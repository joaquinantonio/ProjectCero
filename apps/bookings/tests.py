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
    def test_general_booking_redirects_to_general_enquiry(self):
        response = self.client.get(reverse("bookings:general_request"))

        self.assertRedirects(response, reverse("enquiries:general"))
        self.assertEqual(BookingRequest.objects.count(), 0)

    def test_studio_booking_creates_record_and_sends_email(self):
        response = self.client.post(
            reverse("bookings:request"),
            {
                "request_type": BookingRequest.RequestType.STUDIO,
                "name": "Test User",
                "email": "test@example.com",
                "phone_country_code": "+60",
                "phone": "123456789",
                "preferred_date": "2026-06-15",
                "preferred_time": "11:00",
                "message": "Need a studio session",
            },
        )

        self.assertRedirects(response, reverse("bookings:success"))
        self.assertEqual(BookingRequest.objects.count(), 1)

        booking_request = BookingRequest.objects.first()
        self.assertEqual(booking_request.request_type, BookingRequest.RequestType.STUDIO)

        self.assertEqual(len(mail.outbox), 2)
        self.assertEqual(mail.outbox[1].to, ["test@example.com"])

    def test_invalid_venue_booking_does_not_submit_without_guest_count(self):
        response = self.client.post(
            reverse("bookings:request"),
            {
                "request_type": BookingRequest.RequestType.VENUE,
                "name": "CeroPJ User",
                "email": "venue@example.com",
                "phone_country_code": "+60",
                "phone": "123456789",
                "preferred_date": "2026-06-15",
                "preferred_time": "12:00",
                "message": "Need the venue",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(BookingRequest.objects.count(), 0)
        self.assertEqual(len(mail.outbox), 0)

    def test_honeypot_blocks_submission(self):
        response = self.client.post(
            reverse("bookings:request"),
            {
                "request_type": BookingRequest.RequestType.STUDIO,
                "name": "Spam Bot",
                "email": "spam@example.com",
                "phone_country_code": "+60",
                "phone": "0000000000",
                "preferred_date": "2026-06-15",
                "preferred_time": "11:00",
                "message": "Spam message",
                "website": "http://spam.example.com",
            },
        )

        self.assertRedirects(response, reverse("bookings:success"))
        self.assertEqual(BookingRequest.objects.count(), 0)