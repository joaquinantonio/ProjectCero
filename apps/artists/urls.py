from django.urls import path

from . import views

app_name = "artists"

urlpatterns = [
    path("", views.artist_list_view, name="artist_list"),
    path("<slug:slug>/", views.artist_detail_view, name="artist_detail"),
]