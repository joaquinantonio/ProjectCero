from django import forms

from .models import BookingRequest


class BaseBookingRequestForm(forms.ModelForm):
    website = forms.CharField(
        required=False,
        widget=forms.HiddenInput,
    )

    class Meta:
        model = BookingRequest
        fields = [
            "name",
            "email",
            "phone",
            "preferred_date",
            "preferred_time",
            "guest_count",
            "message",
        ]
        widgets = {
            "preferred_date": forms.DateInput(attrs={"type": "date"}),
            "preferred_time": forms.TimeInput(attrs={"type": "time"}),
            "message": forms.Textarea(attrs={"rows": 5}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Safely set labels, requirements and placeholders only for fields that exist
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

        if "preferred_date" in self.fields:
            self.fields["preferred_date"].label = "Preferred date"
            self.fields["preferred_date"].required = False

        if "preferred_time" in self.fields:
            self.fields["preferred_time"].label = "Preferred time"
            self.fields["preferred_time"].required = False

        if "guest_count" in self.fields:
            self.fields["guest_count"].label = "Estimated guest count"
            self.fields["guest_count"].required = False

        if "message" in self.fields:
            self.fields["message"].label = "Tell us more"
            self.fields["message"].widget.attrs.update(
                {"placeholder": "Share the details of your request"}
            )

    def clean_website(self):
        value = self.cleaned_data.get("website", "")
        if value:
            raise forms.ValidationError("Spam detected.")
        return value


class GeneralBookingRequestForm(BaseBookingRequestForm):
    class Meta(BaseBookingRequestForm.Meta):
        fields = [
            "name",
            "email",
            "phone",
            "message",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["message"].help_text = "Tell us what you need help with."


class StudioBookingRequestForm(BaseBookingRequestForm):
    class Meta(BaseBookingRequestForm.Meta):
        fields = [
            "name",
            "email",
            "phone",
            "preferred_date",
            "preferred_time",
            "message",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["preferred_date"].required = True
        self.fields["message"].help_text = (
            "Tell us what kind of session you want, how many people are involved, "
            "and any important requirements."
        )

    def clean(self):
        cleaned_data = super().clean()
        preferred_date = cleaned_data.get("preferred_date")

        if not preferred_date:
            self.add_error("preferred_date", "Please choose a preferred date.")

        return cleaned_data


class VenueBookingRequestForm(BaseBookingRequestForm):
    class Meta(BaseBookingRequestForm.Meta):
        fields = [
            "name",
            "email",
            "phone",
            "preferred_date",
            "preferred_time",
            "guest_count",
            "message",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["preferred_date"].required = True
        self.fields["guest_count"].required = True
        self.fields["message"].help_text = (
            "Describe the type of event, expected audience, and anything else we should know."
        )

    def clean(self):
        cleaned_data = super().clean()
        preferred_date = cleaned_data.get("preferred_date")
        guest_count = cleaned_data.get("guest_count")

        if not preferred_date:
            self.add_error("preferred_date", "Please choose a preferred date.")

        if not guest_count:
            self.add_error("guest_count", "Please provide an estimated guest count.")

        return cleaned_data