from django.urls import path

from .views import (
    EnquiryLandingView,
    EnquirySuccessView,
    GeneralEnquiryCreateView,
    MerchEnquiryCreateView,
    PaymentEnquiryCreateView,
)

app_name = "enquiries"

urlpatterns = [
    path("", EnquiryLandingView.as_view(), name="landing"),
    path("general/", GeneralEnquiryCreateView.as_view(), name="general"),
    path("merch/", MerchEnquiryCreateView.as_view(), name="merch"),
    path("payment/", PaymentEnquiryCreateView.as_view(), name="payment"),
    path("success/", EnquirySuccessView.as_view(), name="success"),
]