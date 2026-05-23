from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views.generic import CreateView, TemplateView

from apps.events.models import Event
from apps.merch.models import MerchItem
from .forms import GeneralEnquiryForm, MerchEnquiryForm, PaymentEnquiryForm
from .models import EnquirySubmission
from .services import send_enquiry_notification


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
    page_lead = "Use this form for general questions, collaborations, updates, or custom requests."
    sidebar_title = "General enquiries"
    sidebar_body = "Share the details of what you need and any dates or event context if relevant."
    button_label = "Send General Enquiry"


class MerchEnquiryCreateView(BaseEnquiryCreateView):
    form_class = MerchEnquiryForm
    enquiry_type = EnquirySubmission.EnquiryType.MERCH
    eyebrow = "Merchandise Enquiry"
    page_title = "Merchandise Enquiry"
    page_lead = "Use this form to ask about merchandise, availability, or pre-order interest."
    sidebar_title = "Merchandise enquiries"
    sidebar_body = "If you are asking about a specific item, select it below or tell us clearly in your message."
    button_label = "Send merchandise Enquiry"

    def get_initial(self):
        initial = super().get_initial()
        slug = self.request.GET.get("item")
        if slug:
            item = MerchItem.objects.filter(slug=slug, is_active=True).first()
            if item:
                initial["related_merch"] = item.pk
                initial["subject"] = f"Merch enquiry: {item.name}"
        return initial


class PaymentEnquiryCreateView(BaseEnquiryCreateView):
    form_class = PaymentEnquiryForm
    enquiry_type = EnquirySubmission.EnquiryType.PAYMENT
    eyebrow = "Payment Enquiry"
    page_title = "Payment Enquiry"
    page_lead = "Use this form for payment-related questions, package discussions, or manual payment follow-up."
    sidebar_title = "Payment details"
    sidebar_body = "Add the amount, package, event, or any other useful payment context so the team can respond clearly."
    button_label = "Send Payment Enquiry"

    def get_initial(self):
        initial = super().get_initial()
        slug = self.request.GET.get("event")
        if slug:
            event = Event.objects.filter(slug=slug, status=Event.Status.PUBLISHED).first()
            if event:
                initial["related_event"] = event.pk
                initial["subject"] = f"Payment enquiry: {event.title}"
        return initial