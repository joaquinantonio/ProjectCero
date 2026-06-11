from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse, reverse_lazy
from django.views.generic import CreateView, RedirectView, TemplateView

from apps.artists.models import Artist
from apps.events.models import Event
from apps.merch.models import MerchItem

from .forms import (
    ArtistEnquiryForm,
    GeneralEnquiryForm,
    MerchEnquiryForm,
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
    page_lead = "Use this form for general questions, collaborations, partnerships, updates, or custom requests."
    sidebar_title = "General enquiries"
    sidebar_body = "For merch purchases, studio questions, venue questions, or date-specific booking requests, use the dedicated flow so your request goes to the right place."
    button_label = "Send General Enquiry"

    def get_initial(self):
        initial = super().get_initial()

        event_slug = self.request.GET.get("event")
        if event_slug:
            event = Event.objects.filter(slug=event_slug, status=Event.Status.PUBLISHED).first()
            if event:
                initial["related_event"] = event.pk
                initial["subject"] = f"General enquiry: {event.title}"

        return initial


class MerchEnquiryCreateView(BaseEnquiryCreateView):
    form_class = MerchEnquiryForm
    enquiry_type = EnquirySubmission.EnquiryType.MERCH
    eyebrow = "Merch Enquiry"
    page_title = "Enquire to Purchase"
    page_lead = (
        "Select the merch item and quantity you are interested in. "
        "This is not an online purchase form yet; our team will contact you to confirm "
        "availability, payment, and collection or delivery details."
    )
    sidebar_title = "No online payment yet"
    sidebar_body = (
        "CeroPJ is currently handling merch purchases manually. "
        "Submit your details and the team will follow up with payment and fulfilment information."
    )
    button_label = "Send Merch Enquiry"

    def get_merch_item(self):
        slug = self.kwargs.get("slug") or self.request.GET.get("item")

        if not slug:
            return None

        return MerchItem.objects.filter(slug=slug, is_active=True).first()

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        merch_item = self.get_merch_item()

        if merch_item:
            kwargs["locked_merch_item"] = merch_item

        return kwargs

    def get_initial(self):
        initial = super().get_initial()
        merch_item = self.get_merch_item()

        if merch_item:
            initial["related_merch"] = merch_item.pk
            initial["subject"] = f"Merch purchase enquiry: {merch_item.name}"

        return initial

    def form_valid(self, form):
        self.object = form.save(commit=False)
        self.object.enquiry_type = self.enquiry_type

        if not self.object.subject:
            merch_name = self.object.related_merch.name if self.object.related_merch else "Merch"
            self.object.subject = f"Merch purchase enquiry: {merch_name}"

        if self.object.related_merch and not self.object.amount_text:
            self.object.amount_text = self.object.related_merch.price_text

        self.object.save()

        send_enquiry_notification(self.object)

        self.request.session["last_enquiry_reference"] = self.object.reference_code
        return redirect(self.get_success_url())

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
    page_lead = (
        "Use this form to ask about studio services, equipment, session options, "
        "or general studio-related questions."
    )
    sidebar_title = "Studio enquiries"
    sidebar_body = (
        "For specific date and time requests, use the booking request flow. "
        "For general studio questions, send your enquiry here."
    )
    button_label = "Send Studio Enquiry"


class VenueEnquiryCreateView(BaseEnquiryCreateView):
    form_class = VenueEnquiryForm
    enquiry_type = EnquirySubmission.EnquiryType.VENUE
    eyebrow = "Venue Enquiry"
    page_title = "Venue Enquiry"
    page_lead = (
        "Use this form to ask about venue hire, capacity, facilities, event suitability, "
        "or general venue-related questions."
    )
    sidebar_title = "Venue enquiries"
    sidebar_body = (
        "For specific date and time requests, use the booking request flow. "
        "For general venue questions, send your enquiry here."
    )
    button_label = "Send Venue Enquiry"