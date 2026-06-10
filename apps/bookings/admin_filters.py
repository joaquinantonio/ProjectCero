from django.contrib import admin
from django.db import models
from django.utils import timezone

from .models import Booking, BookingRequest


class BookingRequestCalendarStatusFilter(admin.SimpleListFilter):
    title = "calendar status"
    parameter_name = "calendar_status"

    def lookups(self, request, model_admin):
        return (
            ("has_booking", "Has calendar booking"),
            ("needs_booking", "Needs calendar booking"),
            ("missing_time", "Missing preferred date/time"),
        )

    def queryset(self, request, queryset):
        value = self.value()

        if value == "has_booking":
            return queryset.filter(bookings__isnull=False).distinct()

        if value == "needs_booking":
            return queryset.filter(
                request_type__in=[
                    BookingRequest.RequestType.STUDIO,
                    BookingRequest.RequestType.VENUE,
                ],
                bookings__isnull=True,
                preferred_date__isnull=False,
                preferred_start_time__isnull=False,
                preferred_end_time__isnull=False,
            ).distinct()

        if value == "missing_time":
            return queryset.filter(
                request_type__in=[
                    BookingRequest.RequestType.STUDIO,
                    BookingRequest.RequestType.VENUE,
                ],
                bookings__isnull=True,
            ).filter(
                models.Q(preferred_date__isnull=True)
                | models.Q(preferred_start_time__isnull=True)
                | models.Q(preferred_end_time__isnull=True)
            ).distinct()

        return queryset


class BookingScheduleFilter(admin.SimpleListFilter):
    title = "schedule timing"
    parameter_name = "schedule_timing"

    def lookups(self, request, model_admin):
        return (
            ("upcoming", "Upcoming"),
            ("past", "Past"),
            ("today", "Today"),
            ("this_week", "This week"),
            ("blocking", "Blocking availability"),
        )

    def queryset(self, request, queryset):
        value = self.value()
        now = timezone.localtime()
        today = now.date()

        if value == "upcoming":
            return queryset.filter(scheduled_end_at__gte=now)

        if value == "past":
            return queryset.filter(scheduled_end_at__lt=now)

        if value == "today":
            return queryset.filter(scheduled_start_at__date=today)

        if value == "this_week":
            start_of_week = today - timezone.timedelta(days=today.weekday())
            end_of_week = start_of_week + timezone.timedelta(days=7)
            return queryset.filter(
                scheduled_start_at__date__gte=start_of_week,
                scheduled_start_at__date__lt=end_of_week,
            )

        if value == "blocking":
            return queryset.filter(status__in=Booking.BLOCKING_STATUSES)

        return queryset