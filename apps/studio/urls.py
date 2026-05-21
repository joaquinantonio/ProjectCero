from django.urls import path

from . import views

app_name = "studio"

urlpatterns = [
    path("", views.studio_home_view, name="home"),
]