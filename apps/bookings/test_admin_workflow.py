from datetime import date, datetime, time, timedelta

from django.contrib.admin.sites import AdminSite
from django.contrib.auth import get_user_model
from django.contrib.messages.storage.fallback import FallbackStorage
from django.test import RequestFactory, TestCase
from django.utils import timezone

from .admin import BookingAdmin
from .admin_actions import set_booking_status_with_validation
from .availability import get_unavailable_blocks
from .models import Booking, BookingRequest, BookingResource
from .services import (
    assign_default_booking_resource,
    bulk_update_booking_statuses,
    mark_request_as_booking_created,
    prepare_booking_for_save,
    sync_request_status_after_booking_save,
    update_booking_status,
)


class BookingAdminWorkflowTests(TestCase):
    def setUp(self):
        self.resource, _ = BookingResource.objects.get_or_create(
            slug="ceropj-venue",
            defaults={
                "name": "CeroPJ Venue",
                "is_active": True,
                "display_order": 0,
            },
        )

        User = get_user_model()
        self.user = User.objects.create_superuser(
            username="admin",
            email="admin@example.com",
            password="password",
        )

        self.factory = RequestFactory()

    def make_dt(self, hour, minute=0):
        return timezone.make_aware(
            datetime(2026, 6, 15, hour, minute),
            timezone.get_current_timezone(),
        )

    def build_admin_request(self):
        request = self.factory.get("/admin/")
        request.user = self.user
        request.session = self.client.session
        request._messages = FallbackStorage(request)
        return request

    def create_booking(
        self,
        start_hour=13,
        start_minute=0,
        end_hour=14,
        end_minute=0,
        status=Booking.Status.CONFIRMED,
        title="Test Booking",
    ):
        booking = Booking(
            resource=self.resource,
            booking_type=Booking.BookingType.STUDIO,
            title=title,
            scheduled_start_at=self.make_dt(start_hour, start_minute),
            scheduled_end_at=self.make_dt(end_hour, end_minute),
            status=status,
        )
        booking.full_clean()
        booking.save()
        return booking

    def create_booking_request(self, **overrides):
        data = {
            "request_type": BookingRequest.RequestType.STUDIO,
            "name": "Test Customer",
            "email": "customer@example.com",
            "phone": "0123456789",
            "preferred_date": timezone.localdate() + timedelta(days=1),
            "preferred_start_time": time(14, 0),
            "preferred_end_time": time(16, 0),
            "guest_count": 2,
            "message": "I would like to book the studio.",
            "status": BookingRequest.Status.NEW,
        }
        data.update(overrides)
        return BookingRequest.objects.create(**data)

    def create_workflow_booking(self, **overrides):
        start_at = timezone.now() + timedelta(days=2)
        end_at = start_at + timedelta(hours=2)

        data = {
            "resource": self.resource,
            "booking_type": Booking.BookingType.VENUE,
            "scheduled_start_at": start_at,
            "scheduled_end_at": end_at,
            "status": Booking.Status.TENTATIVE,
        }
        data.update(overrides)
        return Booking.objects.create(**data)

    def test_assign_default_booking_resource_sets_resource_when_missing(self):
        booking = Booking(
            booking_type=Booking.BookingType.STUDIO,
            title="Booking Without Resource",
            scheduled_start_at=self.make_dt(13, 0),
            scheduled_end_at=self.make_dt(14, 0),
            status=Booking.Status.TENTATIVE,
        )

        changed = assign_default_booking_resource(booking)

        self.assertTrue(changed)
        self.assertEqual(booking.resource, self.resource)

    def test_assign_default_booking_resource_is_noop_when_resource_exists(self):
        booking = Booking(
            resource=self.resource,
            booking_type=Booking.BookingType.STUDIO,
            title="Booking With Resource",
            scheduled_start_at=self.make_dt(13, 0),
            scheduled_end_at=self.make_dt(14, 0),
            status=Booking.Status.TENTATIVE,
        )

        changed = assign_default_booking_resource(booking)

        self.assertFalse(changed)
        self.assertEqual(booking.resource, self.resource)

    def test_prepare_booking_for_save_assigns_default_resource(self):
        booking = Booking(
            booking_type=Booking.BookingType.STUDIO,
            title="Prepared Booking",
            scheduled_start_at=self.make_dt(13, 0),
            scheduled_end_at=self.make_dt(14, 0),
            status=Booking.Status.TENTATIVE,
        )

        changed = prepare_booking_for_save(booking)

        self.assertTrue(changed)
        self.assertEqual(booking.resource, self.resource)

    def test_booking_admin_save_assigns_default_resource_when_missing(self):
        booking = Booking(
            booking_type=Booking.BookingType.STUDIO,
            title="Studio Booking Without Resource",
            scheduled_start_at=self.make_dt(13, 0),
            scheduled_end_at=self.make_dt(14, 0),
            status=Booking.Status.TENTATIVE,
        )

        booking_admin = BookingAdmin(Booking, AdminSite())
        request = self.build_admin_request()

        booking_admin.save_model(
            request=request,
            obj=booking,
            form=None,
            change=False,
        )

        booking.refresh_from_db()

        self.assertEqual(booking.resource, self.resource)

    def test_update_booking_status_updates_valid_booking(self):
        booking = self.create_booking(
            start_hour=13,
            end_hour=14,
            status=Booking.Status.CANCELLED,
            title="Cancelled Booking",
        )

        update_booking_status(booking, Booking.Status.CONFIRMED)

        booking.refresh_from_db()

        self.assertEqual(booking.status, Booking.Status.CONFIRMED)

    def test_bulk_update_booking_statuses_reports_validation_errors(self):
        self.create_booking(
            start_hour=13,
            end_hour=14,
            status=Booking.Status.CONFIRMED,
            title="Existing Confirmed Booking",
        )

        overlapping_booking = self.create_booking(
            start_hour=13,
            start_minute=30,
            end_hour=14,
            end_minute=30,
            status=Booking.Status.CANCELLED,
            title="Cancelled Overlapping Booking",
        )

        result = bulk_update_booking_statuses(
            Booking.objects.filter(pk=overlapping_booking.pk),
            Booking.Status.CONFIRMED,
        )

        overlapping_booking.refresh_from_db()

        self.assertEqual(result.updated, 0)
        self.assertEqual(result.skipped, 1)
        self.assertEqual(len(result.errors), 1)
        self.assertIn(overlapping_booking.reference_code, result.errors[0])
        self.assertEqual(overlapping_booking.status, Booking.Status.CANCELLED)

    def test_booking_admin_save_converts_linked_request(self):
        booking_request = BookingRequest.objects.create(
            request_type=BookingRequest.RequestType.STUDIO,
            name="Studio Customer",
            email="studio@example.com",
            preferred_date=date(2026, 6, 15),
            preferred_start_time=time(13, 0),
            preferred_end_time=time(14, 0),
            message="Need a studio session",
            status=BookingRequest.Status.IN_REVIEW,
        )

        booking = Booking(
            request=booking_request,
            resource=self.resource,
            booking_type=Booking.BookingType.STUDIO,
            title="Studio Booking",
            scheduled_start_at=self.make_dt(13, 0),
            scheduled_end_at=self.make_dt(14, 0),
            status=Booking.Status.TENTATIVE,
        )

        booking_admin = BookingAdmin(Booking, AdminSite())
        request = self.build_admin_request()

        booking_admin.save_model(
            request=request,
            obj=booking,
            form=None,
            change=False,
        )

        booking_request.refresh_from_db()

        self.assertEqual(Booking.objects.count(), 1)
        self.assertEqual(booking.request, booking_request)
        self.assertEqual(booking_request.status, BookingRequest.Status.CONVERTED)

    def test_booking_request_without_booking_does_not_block_availability(self):
        BookingRequest.objects.create(
            request_type=BookingRequest.RequestType.STUDIO,
            name="Studio Customer",
            email="studio@example.com",
            preferred_date=date(2026, 6, 15),
            preferred_start_time=time(13, 0),
            preferred_end_time=time(14, 0),
            message="Need a studio session",
            status=BookingRequest.Status.CONVERTED,
        )

        blocks = get_unavailable_blocks(
            start_dt=self.make_dt(12, 30),
            end_dt=self.make_dt(14, 30),
            resource=self.resource,
        )

        self.assertEqual(Booking.objects.count(), 0)
        self.assertEqual(blocks, [])

    def test_bulk_confirm_action_does_not_bypass_overlap_validation(self):
        self.create_booking(
            start_hour=13,
            end_hour=14,
            status=Booking.Status.CONFIRMED,
            title="Existing Confirmed Booking",
        )

        overlapping_booking = self.create_booking(
            start_hour=13,
            start_minute=30,
            end_hour=14,
            end_minute=30,
            status=Booking.Status.CANCELLED,
            title="Cancelled Overlapping Booking",
        )

        booking_admin = BookingAdmin(Booking, AdminSite())
        request = self.build_admin_request()

        set_booking_status_with_validation(
            modeladmin=booking_admin,
            request=request,
            queryset=Booking.objects.filter(pk=overlapping_booking.pk),
            target_status=Booking.Status.CONFIRMED,
        )

        overlapping_booking.refresh_from_db()

        self.assertEqual(overlapping_booking.status, Booking.Status.CANCELLED)

    def test_completed_and_no_show_bookings_do_not_block_availability(self):
        self.create_booking(
            start_hour=13,
            end_hour=14,
            status=Booking.Status.COMPLETED,
            title="Completed Booking",
        )

        self.create_booking(
            start_hour=15,
            end_hour=16,
            status=Booking.Status.NO_SHOW,
            title="No Show Booking",
        )

        blocks = get_unavailable_blocks(
            start_dt=self.make_dt(12, 30),
            end_dt=self.make_dt(16, 30),
            resource=self.resource,
        )

        self.assertEqual(blocks, [])

    def test_mark_request_as_booking_created_updates_request_status(self):
        booking_request = self.create_booking_request(
            status=BookingRequest.Status.NEW,
        )

        changed = mark_request_as_booking_created(booking_request)

        booking_request.refresh_from_db()

        self.assertTrue(changed)
        self.assertEqual(
            booking_request.status,
            BookingRequest.Status.CONVERTED,
        )

    def test_mark_request_as_booking_created_is_noop_when_already_converted(self):
        booking_request = self.create_booking_request(
            status=BookingRequest.Status.CONVERTED,
        )

        changed = mark_request_as_booking_created(booking_request)

        booking_request.refresh_from_db()

        self.assertFalse(changed)
        self.assertEqual(
            booking_request.status,
            BookingRequest.Status.CONVERTED,
        )

    def test_sync_request_status_after_booking_save_updates_linked_request(self):
        booking_request = self.create_booking_request(
            status=BookingRequest.Status.NEW,
        )
        booking = self.create_workflow_booking(request=booking_request)

        changed = sync_request_status_after_booking_save(booking)

        booking_request.refresh_from_db()

        self.assertTrue(changed)
        self.assertEqual(
            booking_request.status,
            BookingRequest.Status.CONVERTED,
        )

    def test_sync_request_status_after_booking_save_ignores_unlinked_booking(self):
        booking = self.create_workflow_booking(request=None)

        changed = sync_request_status_after_booking_save(booking)

        self.assertFalse(changed)
