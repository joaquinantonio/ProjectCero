from django.urls import path

from . import views

app_name = "events"

urlpatterns = [
    path("", views.event_list_view, name="event_list"),
    path("past/", views.past_event_list_view, name="past_event_list"),
    path("calendar/", views.event_calendar_view, name="calendar"),
    path("calendar-feed/", views.event_calendar_feed_view, name="calendar_feed"),
    path("calendar.ics", views.event_ics_feed_view, name="calendar_ics"),
    path("<slug:slug>/ics/", views.single_event_ics_feed_view, name="single_event_ics"),
    path("<slug:slug>/", views.event_detail_view, name="event_detail"),
]