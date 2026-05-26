from typing import cast

from django import forms

from apps.events.models import Event
from apps.merch.models import MerchItem
from .models import EnquirySubmission, ArtistEnquiry
from .time_utils import get_time_choices



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

        if "preferred_start_time" in self.fields:
            self.fields["preferred_start_time"].widget = forms.Select(choices=get_time_choices())
            self.fields["preferred_start_time"].label = "Preferred time"

        if "message" in self.fields:
            self.fields["message"].widget = forms.Textarea(attrs={"rows": 5})

        if "related_event" in self.fields:
            cast(forms.ModelChoiceField, self.fields["related_event"]).queryset = Event.objects.filter(
                status=Event.Status.PUBLISHED
            ).order_by("start_at", "title")
            self.fields["related_event"].required = False

        if "related_merch" in self.fields:
            cast(forms.ModelChoiceField, self.fields["related_merch"]).queryset = MerchItem.objects.filter(
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
            "related_merch",
            "amount_text",
            "message",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["subject"].help_text = "A short summary of what you are asking about."
        self.fields["preferred_date"].help_text = "Optional."
        self.fields["related_event"].label = "Related event"
        self.fields["related_event"].help_text = "Optional."
        self.fields["related_merch"].label = "Related merch"
        self.fields["related_merch"].help_text = "Optional."
        self.fields["amount_text"].label = "Amount / package"
        self.fields["amount_text"].help_text = "Optional. Useful for payment follow-up or package discussions."
        self.fields["message"].help_text = "Tell us what you need."
        self.fields["message"].widget.attrs.update(
            {"placeholder": "Share your question, merch details, payment context, collaboration idea, or request"}
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


class StudioEnquiryForm(BaseEnquiryForm):
    class Meta(BaseEnquiryForm.Meta):
        model = EnquirySubmission
        fields = [
            "name",
            "email",
            "phone",
            "subject",
            "preferred_date",
            "preferred_start_time",
            "message",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["subject"].help_text = "A short summary of your studio session request."
        self.fields["preferred_date"].help_text = "Preferred date for your session."
        self.fields["preferred_start_time"].help_text = "Preferred time for your session (30-minute increments)."
        self.fields["message"].help_text = "Tell us about your studio needs and project details."
        self.fields["message"].widget.attrs.update(
            {"placeholder": "Example: duration, equipment needs, type of project"}
        )


class VenueEnquiryForm(BaseEnquiryForm):
    class Meta(BaseEnquiryForm.Meta):
        model = EnquirySubmission
        fields = [
            "name",
            "email",
            "phone",
            "subject",
            "preferred_date",
            "preferred_start_time",
            "message",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["subject"].help_text = "A short summary of your venue hire request."
        self.fields["preferred_date"].help_text = "Preferred date for your event."
        self.fields["preferred_start_time"].help_text = "Preferred time for your event (30-minute increments)."
        self.fields["message"].help_text = "Tell us about your venue needs and event details."
        self.fields["message"].widget.attrs.update(
            {"placeholder": "Example: event type, guest count, duration, special requirements"}
        )


