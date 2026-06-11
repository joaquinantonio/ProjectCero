from datetime import timedelta
from decimal import Decimal
from unittest.mock import patch

from django.test import TestCase
from django.utils import timezone

from apps.artists.models import Artist
from apps.bookings.models import Booking, BookingRequest, BookingResource
from apps.enquiries.models import ArtistEnquiry, EnquirySubmission
from apps.orders.models import Order


class DummyUUID:
    def __init__(self, hex_value):
        self.hex = hex_value


class ReferenceCodeMixinTests(TestCase):
    def create_booking_request(self, **overrides):
        data = {
            "request_type": BookingRequest.RequestType.STUDIO,
            "name": "Test Customer",
            "email": "customer@example.com",
            "phone": "0123456789",
            "message": "I would like to book the studio.",
        }
        data.update(overrides)
        return BookingRequest.objects.create(**data)

    def create_booking(self, **overrides):
        resource = BookingResource.objects.create(
            name="CeroPJ Venue",
            is_active=True,
        )

        start_at = timezone.now() + timedelta(days=1)
        end_at = start_at + timedelta(hours=2)

        data = {
            "resource": resource,
            "booking_type": Booking.BookingType.VENUE,
            "scheduled_start_at": start_at,
            "scheduled_end_at": end_at,
            "status": Booking.Status.TENTATIVE,
        }
        data.update(overrides)
        return Booking.objects.create(**data)

    def create_enquiry_submission(self, **overrides):
        data = {
            "enquiry_type": EnquirySubmission.EnquiryType.GENERAL,
            "name": "General Customer",
            "email": "general@example.com",
            "phone": "0123456789",
            "subject": "General enquiry",
            "message": "I have a question.",
        }
        data.update(overrides)
        return EnquirySubmission.objects.create(**data)

    def create_artist_enquiry(self, **overrides):
        artist = Artist.objects.create(
            name="Test Artist",
            is_active=True,
        )

        data = {
            "name": "Artist Customer",
            "email": "artist@example.com",
            "phone": "0123456789",
            "related_artist": artist,
        }
        data.update(overrides)
        return ArtistEnquiry.objects.create(**data)

    def create_order(self, **overrides):
        data = {
            "customer_name": "Order Customer",
            "customer_email": "order@example.com",
            "customer_phone": "0123456789",
            "status": Order.Status.DRAFT,
            "currency": "MYR",
            "subtotal_amount": Decimal("0.00"),
            "discount_amount": Decimal("0.00"),
            "tax_amount": Decimal("0.00"),
            "total_amount": Decimal("0.00"),
        }
        data.update(overrides)
        return Order.objects.create(**data)

    def test_booking_request_reference_code_uses_bk_prefix(self):
        booking_request = self.create_booking_request()

        self.assertRegex(booking_request.reference_code, r"^BK-[0-9A-F]{8}$")

    def test_booking_reference_code_uses_bkg_prefix(self):
        booking = self.create_booking()

        self.assertRegex(booking.reference_code, r"^BKG-[0-9A-F]{8}$")

    def test_enquiry_submission_reference_code_uses_enq_prefix(self):
        enquiry = self.create_enquiry_submission()

        self.assertRegex(enquiry.reference_code, r"^ENQ-[0-9A-F]{8}$")

    def test_artist_enquiry_reference_code_uses_artq_prefix(self):
        artist_enquiry = self.create_artist_enquiry()

        self.assertRegex(artist_enquiry.reference_code, r"^ARTQ-[0-9A-F]{8}$")

    def test_order_reference_code_uses_ord_prefix(self):
        order = self.create_order()

        self.assertRegex(order.reference_code, r"^ORD-[0-9A-F]{8}$")

    def test_reference_code_generation_retries_after_collision(self):
        self.create_booking_request(reference_code="BK-DUPLICAT")

        with patch(
            "apps.core.models.uuid4",
            side_effect=[
                DummyUUID("duplicat000000000000000000000000"),
                DummyUUID("unique12000000000000000000000000"),
            ],
        ):
            booking_request = self.create_booking_request(
                name="Second Customer",
                email="second@example.com",
            )

        self.assertEqual(booking_request.reference_code, "BK-UNIQUE12")

    def test_save_with_update_fields_includes_generated_reference_code(self):
        booking_request = self.create_booking_request()

        BookingRequest.objects.filter(pk=booking_request.pk).update(reference_code="")

        booking_request.refresh_from_db()
        self.assertEqual(booking_request.reference_code, "")

        booking_request.status = BookingRequest.Status.IN_REVIEW
        booking_request.save(update_fields=["status"])

        booking_request.refresh_from_db()

        self.assertRegex(booking_request.reference_code, r"^BK-[0-9A-F]{8}$")
        self.assertEqual(booking_request.status, BookingRequest.Status.IN_REVIEW)