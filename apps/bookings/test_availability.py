from datetime import datetime

from django.core.exceptions import ValidationError
from django.test import TestCase
from django.utils import timezone

from .availability import find_conflicting_block, get_unavailable_blocks
from .models import Booking, BookingResource


class BookingAvailabilityTests(TestCase):
    def setUp(self):
        self.resource = BookingResource.objects.create(
            name="CeroPJ Venue",
            is_active=True,
        )

    def make_dt(self, hour, minute=0):
        return timezone.make_aware(
            datetime(2026, 6, 15, hour, minute),
            timezone.get_current_timezone(),
        )

    def create_booking(
        self,
        start_hour=11,
        start_minute=0,
        end_hour=12,
        end_minute=0,
        status=Booking.Status.CONFIRMED,
        booking_type=Booking.BookingType.STUDIO,
        title="Test Booking",
    ):
        booking = Booking(
            resource=self.resource,
            booking_type=booking_type,
            title=title,
            scheduled_start_at=self.make_dt(start_hour, start_minute),
            scheduled_end_at=self.make_dt(end_hour, end_minute),
            status=status,
        )
        booking.full_clean()
        booking.save()
        return booking

    def test_booking_reference_code_is_generated(self):
        booking = self.create_booking()

        self.assertTrue(booking.reference_code.startswith("BKG-"))
        self.assertEqual(booking.display_title, "Test Booking")

    def test_studio_booking_must_start_within_business_hours(self):
        booking = Booking(
            resource=self.resource,
            booking_type=Booking.BookingType.STUDIO,
            title="Too Early",
            scheduled_start_at=self.make_dt(10, 0),
            scheduled_end_at=self.make_dt(11, 30),
            status=Booking.Status.CONFIRMED,
        )

        with self.assertRaises(ValidationError):
            booking.full_clean()

    def test_overlapping_blocking_booking_is_rejected(self):
        self.create_booking(
            start_hour=11,
            end_hour=12,
            status=Booking.Status.CONFIRMED,
        )

        overlapping = Booking(
            resource=self.resource,
            booking_type=Booking.BookingType.STUDIO,
            title="Overlap",
            scheduled_start_at=self.make_dt(11, 30),
            scheduled_end_at=self.make_dt(12, 30),
            status=Booking.Status.TENTATIVE,
        )

        with self.assertRaises(ValidationError):
            overlapping.full_clean()

    def test_cancelled_booking_does_not_block_availability(self):
        self.create_booking(
            start_hour=11,
            end_hour=12,
            status=Booking.Status.CANCELLED,
        )

        overlapping = Booking(
            resource=self.resource,
            booking_type=Booking.BookingType.STUDIO,
            title="Allowed",
            scheduled_start_at=self.make_dt(11, 30),
            scheduled_end_at=self.make_dt(12, 30),
            status=Booking.Status.TENTATIVE,
        )

        overlapping.full_clean()

    def test_find_conflicting_block_returns_booking_block(self):
        booking = self.create_booking(
            start_hour=11,
            end_hour=12,
            status=Booking.Status.CONFIRMED,
        )

        conflict = find_conflicting_block(
            start_at=self.make_dt(11, 30),
            end_at=self.make_dt(12, 30),
            resource=self.resource,
        )

        self.assertIsNotNone(conflict)
        self.assertEqual(conflict["type"], "booking")
        self.assertEqual(conflict["object"], booking)

    def test_unavailable_blocks_include_blocking_booking(self):
        booking = self.create_booking(
            start_hour=11,
            end_hour=12,
            status=Booking.Status.CONFIRMED,
        )

        blocks = get_unavailable_blocks(
            start_dt=self.make_dt(10),
            end_dt=self.make_dt(13),
            resource=self.resource,
        )

        self.assertEqual(len(blocks), 1)
        self.assertEqual(blocks[0]["object"], booking)
