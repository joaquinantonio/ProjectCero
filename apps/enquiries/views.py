from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views.generic import CreateView, TemplateView

from apps.artists.models import Artist
from apps.events.models import Event
from apps.merch.models import MerchItem

from .forms import (
    ArtistEnquiryForm,
    GeneralEnquiryForm,
    StudioEnquiryForm,
    VenueEnquiryForm,
)
from .models import EnquirySubmission, ArtistEnquiry
from .services import send_enquiry_notification, send_artist_enquiry_notification


class EnquiryLandingView(TemplateView):
    template_name = "enquiries/enquiry_landing.html"


class EnquirySuccessView(TemplateView):
    template_name = "enquiries/enquiry_success.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["reference_code"] = self.request.session.pop("last_enquiry_reference", None)
        return context


class BaseEnquiryCreateView(CreateView):
    model = EnquirySubmission
    template_name = "enquiries/enquiry_form.html"
    success_url = reverse_lazy("enquiries:success")
    enquiry_type = None
    eyebrow = "Enquire"
    page_title = "Send an Enquiry"
    page_lead = "Send us your details and we will get back to you."
    sidebar_title = "Before you send"
    sidebar_body = "Provide as much useful context as you can so we can respond properly."
    button_label = "Send Enquiry"

    def form_valid(self, form):
        self.object = form.save(commit=False)
        self.object.enquiry_type = self.enquiry_type
        self.object.save()

        send_enquiry_notification(self.object)

        self.request.session["last_enquiry_reference"] = self.object.reference_code
        return redirect(self.get_success_url())

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["eyebrow"] = self.eyebrow
        context["page_title"] = self.page_title
        context["page_lead"] = self.page_lead
        context["sidebar_title"] = self.sidebar_title
        context["sidebar_body"] = self.sidebar_body
        context["button_label"] = self.button_label
        return context


class GeneralEnquiryCreateView(BaseEnquiryCreateView):
    form_class = GeneralEnquiryForm
    enquiry_type = EnquirySubmission.EnquiryType.GENERAL
    eyebrow = "General Enquiry"
    page_title = "General Enquiry"
    page_lead = "Use this form for general questions, collaborations, updates, merch questions, or payment follow-up."
    sidebar_title = "General enquiries"
    sidebar_body = "Share the details of what you need and add any merch or event context if relevant."
    button_label = "Send General Enquiry"

    def get_initial(self):
        initial = super().get_initial()
        item_slug = self.request.GET.get("item")
        if item_slug:
            item = MerchItem.objects.filter(slug=item_slug, is_active=True).first()
            if item:
                initial["related_merch"] = item.pk
                initial["subject"] = f"General enquiry: {item.name}"

        event_slug = self.request.GET.get("event")
        if event_slug:
            event = Event.objects.filter(slug=event_slug, status=Event.Status.PUBLISHED).first()
            if event:
                initial["related_event"] = event.pk
                initial["subject"] = f"General enquiry: {event.title}"

        if self.request.GET.get("amount"):
            initial["amount_text"] = self.request.GET.get("amount")

        return initial


class ArtistEnquiryCreateView(CreateView):
    model = ArtistEnquiry
    form_class = ArtistEnquiryForm
    template_name = "enquiries/artist_enquiry_form.html"
    success_url = reverse_lazy("enquiries:success")

    def get_object(self, queryset=None):
        """Get the artist being enquired about."""
        return get_object_or_404(Artist, slug=self.kwargs["artist_slug"], is_active=True)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["artist"] = self.get_object()
        return context

    def form_valid(self, form):
        self.object = form.save(commit=False)
        self.object.related_artist = self.get_object()
        self.object.full_clean()  # Trigger model validation
        self.object.save()

        send_artist_enquiry_notification(self.object)

        self.request.session["last_enquiry_reference"] = self.object.reference_code
        return redirect(self.get_success_url())


class StudioEnquiryCreateView(BaseEnquiryCreateView):
    form_class = StudioEnquiryForm
    enquiry_type = EnquirySubmission.EnquiryType.STUDIO
    eyebrow = "Studio Enquiry"
    page_title = "Studio Enquiry"
    page_lead = "Use this form to enquire about studio sessions, book your preferred date and time, or ask about equipment and services."
    sidebar_title = "Studio enquiries"
    sidebar_body = "Tell us about your project, your preferred date and time, and any specific equipment or service needs."
    button_label = "Send Studio Enquiry"


class VenueEnquiryCreateView(BaseEnquiryCreateView):
    form_class = VenueEnquiryForm
    enquiry_type = EnquirySubmission.EnquiryType.VENUE
    eyebrow = "Venue Enquiry"
    page_title = "Venue Enquiry"
    page_lead = "Use this form to enquire about venue hire, book your preferred date and time, or ask about capacity and facilities."
    sidebar_title = "Venue enquiries"
    sidebar_body = "Tell us about your event, preferred date and time, guest count, and any special requirements you may have."
    button_label = "Send Venue Enquiry"
