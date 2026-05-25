from django.urls import path

from . import views

app_name = "studio"

urlpatterns = [
    path("", views.studio_home_view, name="home"),
    path("equipment/", views.equipment_list_view, name="equipment_list"),
    path("<slug:slug>/", views.studio_service_detail_view, name="service_detail"),
]