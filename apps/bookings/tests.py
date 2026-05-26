from datetime import date, time, timedelta

from django.core import mail
from django.test import TestCase, override_settings
from django.urls import reverse

from .availability import get_unavailable_blocks
from .calendar_workflow import create_calendar_booking_from_request
from .forms import CombinedBookingRequestForm
from .models import Booking, BookingRequest, BookingResource


@override_settings(
    EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
    BOOKING_NOTIFICATION_EMAIL="notify@example.com",
    DEFAULT_FROM_EMAIL="no-reply@example.com",
)
class BookingRequestTests(TestCase):
    def test_preferred_start_time_dropdown_includes_midnight_next_day_option(self):
        form = CombinedBookingRequestForm()

        # Check the widget choices, not the field choices
        widget_choices = form.fields["preferred_start_time"].widget.choices
        self.assertIn(("23:59", "11:59 PM (midnight next day)"), widget_choices)

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
                "preferred_start_time": "11:00",
                "message": "Need a studio session",
            },
        )

        self.assertRedirects(response, reverse("bookings:success"))
        self.assertEqual(BookingRequest.objects.count(), 1)

        booking_request = BookingRequest.objects.first()
        self.assertEqual(booking_request.request_type, BookingRequest.RequestType.STUDIO)
        self.assertEqual(booking_request.preferred_start_time.strftime("%H:%M"), "11:00")

        self.assertEqual(len(mail.outbox), 2)
        self.assertEqual(mail.outbox[1].to, ["test@example.com"])

    def test_studio_booking_accepts_midnight_next_day_time(self):
        response = self.client.post(
            reverse("bookings:request"),
            {
                "request_type": BookingRequest.RequestType.STUDIO,
                "name": "Late Studio User",
                "email": "late@example.com",
                "phone_country_code": "+60",
                "phone": "123456789",
                "preferred_date": "2026-06-15",
                "preferred_start_time": "23:59",
                "message": "Need a late studio session",
            },
        )

        self.assertRedirects(response, reverse("bookings:success"))
        booking_request = BookingRequest.objects.get(email="late@example.com")
        self.assertEqual(booking_request.preferred_start_time.strftime("%H:%M"), "23:59")

    def test_venue_booking_accepts_midnight_next_day_time(self):
        response = self.client.post(
            reverse("bookings:request"),
            {
                "request_type": BookingRequest.RequestType.VENUE,
                "name": "Late Venue User",
                "email": "venue-late@example.com",
                "phone_country_code": "+60",
                "phone": "123456789",
                "preferred_date": "2026-06-15",
                "preferred_start_time": "23:59",
                "guest_count": "40",
                "message": "Need a late venue request",
            },
        )

        self.assertRedirects(response, reverse("bookings:success"))
        booking_request = BookingRequest.objects.get(email="venue-late@example.com")
        self.assertEqual(booking_request.request_type, BookingRequest.RequestType.VENUE)
        self.assertEqual(booking_request.preferred_start_time.strftime("%H:%M"), "23:59")

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
                "preferred_start_time": "12:00",
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
                "preferred_start_time": "11:00",
                "message": "Spam message",
                "website": "http://spam.example.com",
            },
        )

        self.assertRedirects(response, reverse("bookings:success"))
        self.assertEqual(BookingRequest.objects.count(), 0)


class CalendarBookingWorkflowTests(TestCase):
    def setUp(self):
        self.resource = BookingResource.objects.create(
            name="CeroPJ Venue",
            slug="ceropj-venue",
            is_active=True,
            display_order=0,
        )

    def test_confirmed_studio_request_can_create_calendar_booking(self):
        booking_request = BookingRequest.objects.create(
            request_type=BookingRequest.RequestType.STUDIO,
            name="Studio Customer",
            email="studio@example.com",
            preferred_date=date(2026, 6, 15),
            preferred_start_time=time(13, 0),
            message="Need a studio session",
            status=BookingRequest.Status.CONFIRMED,
        )

        booking, message = create_calendar_booking_from_request(
            booking_request,
            status=Booking.Status.CONFIRMED,
        )

        self.assertIsNotNone(booking)
        self.assertEqual(booking.booking_type, Booking.BookingType.STUDIO)
        self.assertEqual(booking.resource, self.resource)
        self.assertEqual(booking.status, Booking.Status.CONFIRMED)
        self.assertEqual(booking.request, booking_request)
        self.assertIn("Calendar booking created", message)

    def test_calendar_booking_blocks_public_unavailable_feed_source(self):
        booking_request = BookingRequest.objects.create(
            request_type=BookingRequest.RequestType.STUDIO,
            name="Studio Customer",
            email="studio@example.com",
            preferred_date=date(2026, 6, 15),
            preferred_start_time=time(13, 0),
            message="Need a studio session",
            status=BookingRequest.Status.CONFIRMED,
        )

        booking, _ = create_calendar_booking_from_request(
            booking_request,
            status=Booking.Status.CONFIRMED,
        )

        blocks = get_unavailable_blocks(
            start_dt=booking.scheduled_start_at - timedelta(minutes=30),
            end_dt=booking.scheduled_end_at + timedelta(minutes=30),
        )

        self.assertTrue(
            any(
                block["type"] == "booking"
                and block["object"].pk == booking.pk
                for block in blocks
            )
        )

    def test_request_without_preferred_start_time_does_not_create_booking(self):
        booking_request = BookingRequest.objects.create(
            request_type=BookingRequest.RequestType.STUDIO,
            name="Studio Customer",
            email="studio@example.com",
            preferred_date=date(2026, 6, 15),
            message="Need a studio session",
            status=BookingRequest.Status.CONFIRMED,
        )

        booking, message = create_calendar_booking_from_request(
            booking_request,
            status=Booking.Status.CONFIRMED,
        )

        self.assertIsNone(booking)
        self.assertIn("Preferred date and preferred time are required", message)
        self.assertEqual(Booking.objects.count(), 0)
