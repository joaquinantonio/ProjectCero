from django.contrib import admin, messages
from django.core.exceptions import ValidationError

from apps.core.admin import make_bulk_update_action

from .models import Booking, BookingRequest


mark_in_review = make_bulk_update_action(
    action_name="mark_in_review",
    field_name="status",
    value=BookingRequest.Status.IN_REVIEW,
    description="Mark selected requests as In Review",
    success_message="{updated} request(s) marked as In Review.",
)

mark_contacted = make_bulk_update_action(
    action_name="mark_contacted",
    field_name="status",
    value=BookingRequest.Status.CONTACTED,
    description="Mark selected requests as Contacted",
    success_message="{updated} request(s) marked as Contacted.",
)

mark_closed = make_bulk_update_action(
    action_name="mark_closed",
    field_name="status",
    value=BookingRequest.Status.CLOSED,
    description="Mark selected requests as Closed",
    success_message="{updated} request(s) marked as Closed.",
)

mark_cancelled = make_bulk_update_action(
    action_name="mark_cancelled",
    field_name="status",
    value=BookingRequest.Status.CANCELLED,
    description="Mark selected requests as Cancelled",
    success_message="{updated} request(s) marked as Cancelled.",
)


def set_booking_status_with_validation(modeladmin, request, queryset, target_status):
    updated = 0
    skipped = 0
    errors = []

    for booking in queryset:
        booking.status = target_status

        try:
            if target_status in Booking.BLOCKING_STATUSES:
                booking.full_clean()

            booking.save(update_fields=["status", "updated_at"])
            updated += 1

        except ValidationError as exc:
            skipped += 1
            error_text = exc.messages[0] if exc.messages else str(exc)
            errors.append(f"{booking.reference_code}: {error_text}")

    if updated:
        modeladmin.message_user(
            request,
            f"{updated} booking(s) updated to {Booking.Status(target_status).label}.",
            messages.SUCCESS,
        )

    if skipped:
        modeladmin.message_user(
            request,
            f"{skipped} booking(s) could not be updated because of validation errors.",
            messages.WARNING,
        )

    for error in errors[:5]:
        modeladmin.message_user(request, error, messages.ERROR)

    if len(errors) > 5:
        modeladmin.message_user(
            request,
            f"{len(errors) - 5} more validation error(s) were not shown.",
            messages.ERROR,
        )


@admin.action(description="Mark selected bookings as Tentative")
def mark_bookings_tentative(modeladmin, request, queryset):
    set_booking_status_with_validation(
        modeladmin,
        request,
        queryset,
        Booking.Status.TENTATIVE,
    )


@admin.action(description="Mark selected bookings as Confirmed")
def mark_bookings_confirmed(modeladmin, request, queryset):
    set_booking_status_with_validation(
        modeladmin,
        request,
        queryset,
        Booking.Status.CONFIRMED,
    )


@admin.action(description="Mark selected bookings as Cancelled")
def mark_bookings_cancelled(modeladmin, request, queryset):
    set_booking_status_with_validation(
        modeladmin,
        request,
        queryset,
        Booking.Status.CANCELLED,
    )


@admin.action(description="Mark selected bookings as Completed")
def mark_bookings_completed(modeladmin, request, queryset):
    set_booking_status_with_validation(
        modeladmin,
        request,
        queryset,
        Booking.Status.COMPLETED,
    )


@admin.action(description="Mark selected bookings as No Show")
def mark_bookings_no_show(modeladmin, request, queryset):
    set_booking_status_with_validation(
        modeladmin,
        request,
        queryset,
        Booking.Status.NO_SHOW,
    )