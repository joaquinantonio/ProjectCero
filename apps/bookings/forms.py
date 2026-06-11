from django import forms

from .models import BookingRequest

COUNTRY_CODE_CHOICES = [
    # Malaysia first
    ("+60", "Malaysia (+60)"),

    # ASEAN countries
    ("+673", "Brunei (+673)"),
    ("+855", "Cambodia (+855)"),
    ("+62", "Indonesia (+62)"),
    ("+856", "Laos (+856)"),
    ("+95", "Myanmar (+95)"),
    ("+63", "Philippines (+63)"),
    ("+65", "Singapore (+65)"),
    ("+66", "Thailand (+66)"),
    ("+670", "Timor-Leste (+670)"),
    ("+84", "Vietnam (+84)"),

    # Rest of the countries in alphabetical order
    ("+93", "Afghanistan (+93)"),
    ("+355", "Albania (+355)"),
    ("+213", "Algeria (+213)"),
    ("+376", "Andorra (+376)"),
    ("+244", "Angola (+244)"),
    ("+54", "Argentina (+54)"),
    ("+374", "Armenia (+374)"),
    ("+61", "Australia (+61)"),
    ("+43", "Austria (+43)"),
    ("+994", "Azerbaijan (+994)"),
    ("+973", "Bahrain (+973)"),
    ("+880", "Bangladesh (+880)"),
    ("+32", "Belgium (+32)"),
    ("+501", "Belize (+501)"),
    ("+229", "Benin (+229)"),
    ("+975", "Bhutan (+975)"),
    ("+591", "Bolivia (+591)"),
    ("+387", "Bosnia and Herzegovina (+387)"),
    ("+267", "Botswana (+267)"),
    ("+55", "Brazil (+55)"),
    ("+359", "Bulgaria (+359)"),
    ("+237", "Cameroon (+237)"),
    ("+1", "Canada / United States (+1)"),
    ("+56", "Chile (+56)"),
    ("+86", "China (+86)"),
    ("+57", "Colombia (+57)"),
    ("+506", "Costa Rica (+506)"),
    ("+385", "Croatia (+385)"),
    ("+357", "Cyprus (+357)"),
    ("+420", "Czech Republic (+420)"),
    ("+45", "Denmark (+45)"),
    ("+20", "Egypt (+20)"),
    ("+372", "Estonia (+372)"),
    ("+251", "Ethiopia (+251)"),
    ("+358", "Finland (+358)"),
    ("+33", "France (+33)"),
    ("+995", "Georgia (+995)"),
    ("+49", "Germany (+49)"),
    ("+233", "Ghana (+233)"),
    ("+30", "Greece (+30)"),
    ("+852", "Hong Kong (+852)"),
    ("+36", "Hungary (+36)"),
    ("+354", "Iceland (+354)"),
    ("+91", "India (+91)"),
    ("+98", "Iran (+98)"),
    ("+964", "Iraq (+964)"),
    ("+353", "Ireland (+353)"),
    ("+972", "Israel (+972)"),
    ("+39", "Italy (+39)"),
    ("+81", "Japan (+81)"),
    ("+962", "Jordan (+962)"),
    ("+7", "Kazakhstan / Russia (+7)"),
    ("+254", "Kenya (+254)"),
    ("+965", "Kuwait (+965)"),
    ("+371", "Latvia (+371)"),
    ("+961", "Lebanon (+961)"),
    ("+218", "Libya (+218)"),
    ("+370", "Lithuania (+370)"),
    ("+352", "Luxembourg (+352)"),
    ("+853", "Macau (+853)"),
    ("+261", "Madagascar (+261)"),
    ("+960", "Maldives (+960)"),
    ("+356", "Malta (+356)"),
    ("+230", "Mauritius (+230)"),
    ("+52", "Mexico (+52)"),
    ("+373", "Moldova (+373)"),
    ("+377", "Monaco (+377)"),
    ("+976", "Mongolia (+976)"),
    ("+212", "Morocco (+212)"),
    ("+977", "Nepal (+977)"),
    ("+31", "Netherlands (+31)"),
    ("+64", "New Zealand (+64)"),
    ("+234", "Nigeria (+234)"),
    ("+47", "Norway (+47)"),
    ("+968", "Oman (+968)"),
    ("+92", "Pakistan (+92)"),
    ("+507", "Panama (+507)"),
    ("+675", "Papua New Guinea (+675)"),
    ("+51", "Peru (+51)"),
    ("+48", "Poland (+48)"),
    ("+351", "Portugal (+351)"),
    ("+974", "Qatar (+974)"),
    ("+40", "Romania (+40)"),
    ("+966", "Saudi Arabia (+966)"),
    ("+381", "Serbia (+381)"),
    ("+421", "Slovakia (+421)"),
    ("+386", "Slovenia (+386)"),
    ("+27", "South Africa (+27)"),
    ("+82", "South Korea (+82)"),
    ("+34", "Spain (+34)"),
    ("+94", "Sri Lanka (+94)"),
    ("+46", "Sweden (+46)"),
    ("+41", "Switzerland (+41)"),
    ("+886", "Taiwan (+886)"),
    ("+255", "Tanzania (+255)"),
    ("+90", "Turkey (+90)"),
    ("+256", "Uganda (+256)"),
    ("+380", "Ukraine (+380)"),
    ("+971", "United Arab Emirates (+971)"),
    ("+44", "United Kingdom (+44)"),
    ("+598", "Uruguay (+598)"),
    ("+998", "Uzbekistan (+998)"),
    ("+58", "Venezuela (+58)"),
    ("+967", "Yemen (+967)"),
    ("+260", "Zambia (+260)"),
    ("+263", "Zimbabwe (+263)"),
]


def build_time_label(hour, minute):
    display_hour = hour
    suffix = "AM"

    if hour == 12:
        display_hour = 12
        suffix = "PM"
    elif hour > 12:
        display_hour = hour - 12
        suffix = "PM"

    return f"{display_hour}:{minute:02d} {suffix}"


def build_booking_start_time_choices():
    choices = [("", "Select start time")]

    for hour in range(11, 24):
        for minute in (0, 30):
            value = f"{hour:02d}:{minute:02d}"
            choices.append((value, build_time_label(hour, minute)))

    if ("23:59", "11:59 PM (midnight next day)") not in choices:
        choices.append(("23:59", "11:59 PM (midnight next day)"))

    return choices


def build_booking_end_time_choices():
    choices = [("", "Select end time")]

    for hour in range(11, 24):
        for minute in (0, 30):
            if hour == 11 and minute == 0:
                continue
            value = f"{hour:02d}:{minute:02d}"
            choices.append((value, build_time_label(hour, minute)))

    choices.append(("23:59", "11:59 PM (midnight next day)"))
    return choices


class BaseBookingRequestForm(forms.ModelForm):
    website = forms.CharField(required=False, widget=forms.HiddenInput)

    class Meta:
        model = BookingRequest
        fields = [
            "name",
            "email",
            "phone",
            "preferred_date",
            "preferred_start_time",
            "preferred_end_time",
            "guest_count",
            "message",
        ]
        widgets = {
            "preferred_date": forms.DateInput(attrs={"type": "date"}),
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

        if "preferred_start_time" in self.fields:
            self.fields["preferred_start_time"].label = "Start time"
            self.fields["preferred_start_time"].required = False
            self.fields["preferred_start_time"].help_text = "Optional."

        if "preferred_end_time" in self.fields:
            self.fields["preferred_end_time"].label = "End time"
            self.fields["preferred_end_time"].required = False
            self.fields["preferred_end_time"].help_text = "Optional."

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
        widget=forms.Select(attrs={"class": "js-compact-select"}),
    )

    preferred_start_time = forms.TimeField(
        required=False,
        widget=forms.Select(
            choices=build_booking_start_time_choices(),
            attrs={"class": "js-compact-select"},
        ),
        input_formats=["%H:%M"],
    )

    preferred_end_time = forms.TimeField(
        required=False,
        widget=forms.Select(
            choices=build_booking_end_time_choices(),
            attrs={"class": "js-compact-select"},
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
            "preferred_start_time",
            "preferred_end_time",
            "guest_count",
            "message",
        ]
        widgets = {
            **BaseBookingRequestForm.Meta.widgets,
            "request_type": forms.Select(attrs={"class": "js-compact-select"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["request_type"].label = "Booking type"
        self.fields["request_type"].choices = [
            (BookingRequest.RequestType.STUDIO, "Studio session"),
            (BookingRequest.RequestType.VENUE, "Venue"),
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

        self.fields["preferred_start_time"].label = "Start time"
        self.fields["preferred_start_time"].required = True
        self.fields["preferred_start_time"].help_text = (
            "Required. Choose a start time from 11:00 AM onwards."
        )

        self.fields["preferred_end_time"].label = "End time"
        self.fields["preferred_end_time"].required = True
        self.fields["preferred_end_time"].help_text = (
            "Required. Latest same-day end time is 11:59 PM."
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
        preferred_start_time = cleaned_data.get("preferred_start_time")
        preferred_end_time = cleaned_data.get("preferred_end_time")
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

        if not preferred_start_time:
            self.add_error("preferred_start_time", "Please choose a start time.")

        if not preferred_end_time:
            self.add_error("preferred_end_time", "Please choose an end time.")

        if preferred_start_time and preferred_end_time:
            if preferred_end_time <= preferred_start_time:
                self.add_error(
                    "preferred_end_time",
                    "End time must be after start time.",
                )
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

    def save(self, commit=True):
        instance = super().save(commit=False)

        if commit:
            instance.save()
            self.save_m2m()

        return instance
