from django import forms

from apps.events.models import Event
from apps.merch.models import MerchItem
from .models import EnquirySubmission, ArtistEnquiry



class BaseEnquiryForm(forms.ModelForm):
    website = forms.CharField(required=False, widget=forms.HiddenInput)

    class Meta:
        model = EnquirySubmission
        fields = []

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if "name" in self.fields:
            self.fields["name"].label = "Your name"
            self.fields["name"].widget.attrs.update({"placeholder": "Your full name"})

        if "email" in self.fields:
            self.fields["email"].label = "Email address"
            self.fields["email"].widget.attrs.update({"placeholder": "you@example.com"})

        if "phone" in self.fields:
            self.fields["phone"].label = "Phone / WhatsApp"
            self.fields["phone"].required = False
            self.fields["phone"].widget.attrs.update({"placeholder": "+60..."})
            self.fields["phone"].help_text = "Optional."

        if "subject" in self.fields:
            self.fields["subject"].widget.attrs.update({"placeholder": "Short summary of your enquiry"})

        if "preferred_date" in self.fields:
            self.fields["preferred_date"].widget = forms.DateInput(attrs={"type": "date"})

        if "message" in self.fields:
            self.fields["message"].widget = forms.Textarea(attrs={"rows": 5})

        if "related_event" in self.fields:
            self.fields["related_event"].queryset = Event.objects.filter(
                status=Event.Status.PUBLISHED
            ).order_by("start_at", "title")
            self.fields["related_event"].required = False

        if "related_merch" in self.fields:
            self.fields["related_merch"].queryset = MerchItem.objects.filter(
                is_active=True
            ).order_by("display_order", "name")
            self.fields["related_merch"].required = False

    def clean(self):
        cleaned_data = super().clean()
        if cleaned_data.get("website"):
            raise forms.ValidationError("Spam detected.")
        return cleaned_data


class GeneralEnquiryForm(BaseEnquiryForm):
    class Meta(BaseEnquiryForm.Meta):
        model = EnquirySubmission
        fields = [
            "name",
            "email",
            "phone",
            "subject",
            "preferred_date",
            "related_event",
            "message",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["subject"].help_text = "A short summary of what you are asking about."
        self.fields["preferred_date"].help_text = "Optional."
        self.fields["related_event"].label = "Related event"
        self.fields["related_event"].help_text = "Optional."
        self.fields["message"].help_text = "Tell us what you need."
        self.fields["message"].widget.attrs.update(
            {"placeholder": "Share your question, collaboration idea, or request"}
        )


class MerchEnquiryForm(BaseEnquiryForm):
    class Meta(BaseEnquiryForm.Meta):
        model = EnquirySubmission
        fields = [
            "name",
            "email",
            "phone",
            "subject",
            "related_merch",
            "message",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["related_merch"].label = "Merchandise"
        self.fields["related_merch"].help_text = "Optional."
        self.fields["message"].help_text = "Tell us which item you are asking about and what you need."
        self.fields["message"].widget.attrs.update(
            {"placeholder": "Example: interested in availability, size, pre-order, or collection details"}
        )


class PaymentEnquiryForm(BaseEnquiryForm):
    class Meta(BaseEnquiryForm.Meta):
        model = EnquirySubmission
        fields = [
            "name",
            "email",
            "phone",
            "subject",
            "related_event",
            "amount_text",
            "message",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["related_event"].label = "Related event"
        self.fields["related_event"].help_text = "Optional."
        self.fields["amount_text"].label = "Amount / package"
        self.fields["amount_text"].help_text = "Optional. Example: RM50 deposit, RM120 package, or leave blank."
        self.fields["amount_text"].widget.attrs.update({"placeholder": "Optional"})
        self.fields["message"].help_text = "Add any payment details, proof notes, or questions."
        self.fields["message"].widget.attrs.update(
            {"placeholder": "Example: asking about deposit, balance payment, package pricing, or proof of transfer"}
        )


class ArtistEnquiryForm(forms.ModelForm):
    """Form for enquiring about/contacting artists."""
    
    website = forms.CharField(required=False, widget=forms.HiddenInput)

    class Meta:
        model = ArtistEnquiry
        fields = ["name", "email", "phone"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["name"].label = "Your name"
        self.fields["name"].widget.attrs.update({"placeholder": "Your full name"})

        self.fields["email"].label = "Email address"
        self.fields["email"].widget.attrs.update({"placeholder": "you@example.com"})

        self.fields["phone"].label = "WhatsApp / Phone"
        self.fields["phone"].widget.attrs.update({"placeholder": "+60..."})
        self.fields["phone"].help_text = "So we can reach you directly"

    def clean(self):
        cleaned_data = super().clean()
        if cleaned_data.get("website"):
            raise forms.ValidationError("Spam detected.")
        return cleaned_data
