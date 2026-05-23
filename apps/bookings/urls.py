from django.urls import path

from . import views

app_name = "bookings"

urlpatterns = [
    path("", views.booking_landing_view, name="landing"),
    path("contact/", views.general_booking_request_view, name="general_request"),
    path("studio/", views.studio_booking_request_view, name="studio_request"),
    path("studio/unavailable/", views.studio_unavailable_feed_view, name="studio_unavailable_feed"),
    path("venue/", views.venue_booking_request_view, name="venue_request"),
    path("success/", views.booking_success_view, name="success"),
]