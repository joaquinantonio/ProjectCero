from django.urls import path

from .views import MerchDetailView, MerchEnquiryRedirectView, MerchListView

app_name = "merch"

urlpatterns = [
    path("", MerchListView.as_view(), name="merch_list"),
    path("<slug:slug>/enquire/", MerchEnquiryRedirectView.as_view(), name="merch_enquire"),
    path("<slug:slug>/", MerchDetailView.as_view(), name="merch_detail"),
]