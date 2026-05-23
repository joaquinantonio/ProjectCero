from django import forms

from .models import BookingRequest

COUNTRY_CODE_CHOICES = [
    ("+60", "Malaysia (+60)"),
    ("+65", "Singapore (+65)"),
    ("+62", "Indonesia (+62)"),
    ("+66", "Thailand (+66)"),
    ("+63", "Philippines (+63)"),
    ("+673", "Brunei (+673)"),
    ("+91", "India (+91)"),
    ("+971", "United Arab Emirates (+971)"),
    ("+44", "United Kingdom (+44)"),
    ("+1", "United States / Canada (+1)"),
    ("+61", "Australia (+61)"),
    ("+81", "Japan (+81)"),
    ("+82", "South Korea (+82)"),
    ("+86", "China (+86)"),
]


def build_preferred_time_choices():
    choices = [("", "Select preferred time")]

    # Public request time options.
    # Studio business hours are 11:00 AM to 12:00 midnight.
    for hour in range(11, 24):
        for minute in (0, 30):
            value = f"{hour:02d}:{minute:02d}"

            display_hour = hour
            suffix = "AM"

            if hour == 12:
                display_hour = 12
                suffix = "PM"
            elif hour > 12:
                display_hour = hour - 12
                suffix = "PM"

            label = f"{display_hour}:{minute:02d} {suffix}"
            choices.append((value, label))

    return choices


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

        if "preferred_date" in self.fields:
            self.fields["preferred_date"].label = "Preferred date"
            self.fields["preferred_date"].required = False

        if "preferred_time" in self.fields:
            self.fields["preferred_time"].label = "Preferred time"
            self.fields["preferred_time"].required = False
            self.fields["preferred_time"].help_text = "Optional."

        if "guest_count" in self.fields:
            self.fields["guest_count"].label = "Estimated guest count"
            self.fields["guest_count"].required = False
            self.fields["guest_count"].help_text = "Optional."

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


class CombinedBookingRequestForm(BaseBookingRequestForm):
    phone_country_code = forms.ChoiceField(
        choices=COUNTRY_CODE_CHOICES,
        initial="+60",
        required=False,
        label="Country code",
        widget=forms.Select(
            attrs={
                "class": "js-compact-select",
            }
        ),
    )

    preferred_time = forms.TimeField(
        required=False,
        widget=forms.Select(
            choices=build_preferred_time_choices(),
            attrs={
                "class": "js-compact-select",
            },
        ),
        input_formats=["%H:%M"],
    )

    class Meta(BaseBookingRequestForm.Meta):
        fields = [
            "request_type",
            "name",
            "email",
            "phone_country_code",
            "phone",
            "preferred_date",
            "preferred_time",
            "guest_count",
            "message",
        ]
        widgets = {
            **BaseBookingRequestForm.Meta.widgets,
            "request_type": forms.Select(
                attrs={
                    "class": "js-compact-select",
                }
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["request_type"].label = "Booking type"
        self.fields["request_type"].choices = [
            (BookingRequest.RequestType.STUDIO, "Studio session"),
            (BookingRequest.RequestType.VENUE, "Venue / event space"),
        ]
        self.fields["request_type"].required = True
        self.fields["request_type"].help_text = (
            "Choose whether this request is for the studio or venue."
        )

        self.fields["phone_country_code"].help_text = (
            "Select your WhatsApp / phone country code."
        )

        self.fields["phone"].label = "Phone / WhatsApp number"
        self.fields["phone"].required = False
        self.fields["phone"].help_text = (
            "Optional. Enter the number without the country code."
        )
        self.fields["phone"].widget.attrs.update(
            {
                "placeholder": "Example: 123456789",
                "inputmode": "tel",
                "autocomplete": "tel-national",
            }
        )

        self.fields["preferred_date"].required = True
        self.fields["preferred_date"].help_text = "Required."

        self.fields["preferred_time"].label = "Preferred time"
        self.fields["preferred_time"].required = False
        self.fields["preferred_time"].help_text = (
            "Optional. Choose a preferred time from the dropdown."
        )

        self.fields["guest_count"].required = False
        self.fields["guest_count"].help_text = "Required for venue bookings."

        self.fields["message"].label = "Tell us more"
        self.fields["message"].help_text = (
            "Tell us what you need, the purpose of the booking, "
            "and any important requirements."
        )
        self.fields["message"].widget.attrs.update(
            {
                "placeholder": (
                    "Example: Studio recording for 2 people, or private event "
                    "for 60 guests with basic sound setup."
                )
            }
        )

    def clean(self):
        cleaned_data = super().clean()

        request_type = cleaned_data.get("request_type")
        preferred_date = cleaned_data.get("preferred_date")
        guest_count = cleaned_data.get("guest_count")

        country_code = cleaned_data.get("phone_country_code")
        phone = cleaned_data.get("phone", "")

        allowed_types = [
            BookingRequest.RequestType.STUDIO,
            BookingRequest.RequestType.VENUE,
        ]

        if request_type not in allowed_types:
            self.add_error("request_type", "Please choose studio or venue.")

        if not preferred_date:
            self.add_error("preferred_date", "Please choose a preferred date.")

        if request_type == BookingRequest.RequestType.VENUE and not guest_count:
            self.add_error(
                "guest_count",
                "Please provide an estimated guest count for venue bookings.",
            )

        if phone:
            normalized_phone = (
                phone.strip()
                .replace(" ", "")
                .replace("-", "")
                .replace("(", "")
                .replace(")", "")
            )

            if normalized_phone.startswith("+"):
                cleaned_data["phone"] = normalized_phone
            else:
                normalized_phone = normalized_phone.lstrip("0")

                if country_code:
                    cleaned_data["phone"] = f"{country_code}{normalized_phone}"
                else:
                    cleaned_data["phone"] = normalized_phone

        return cleaned_data