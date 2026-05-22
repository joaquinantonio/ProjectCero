from django.urls import path

from .views import MerchDetailView, MerchListView

app_name = "merch"

urlpatterns = [
    path("", MerchListView.as_view(), name="merch_list"),
    path("<slug:slug>/", MerchDetailView.as_view(), name="merch_detail"),
]