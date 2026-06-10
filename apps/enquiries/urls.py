from django.urls import path

from .views import (
    EnquiryLandingView,
    EnquirySuccessView,
    GeneralEnquiryCreateView,
    MerchEnquiryCreateView,
    ArtistEnquiryCreateView,
    StudioEnquiryCreateView,
    VenueEnquiryCreateView,
)

app_name = "enquiries"

urlpatterns = [
    path("", EnquiryLandingView.as_view(), name="landing"),
    path("general/", GeneralEnquiryCreateView.as_view(), name="general"),
    path("merch/", MerchEnquiryCreateView.as_view(), name="merch"),
    path("studio/", StudioEnquiryCreateView.as_view(), name="studio"),
    path("venue/", VenueEnquiryCreateView.as_view(), name="venue"),
    path("artist/<slug:artist_slug>/", ArtistEnquiryCreateView.as_view(), name="artist"),
    path("success/", EnquirySuccessView.as_view(), name="success"),
]