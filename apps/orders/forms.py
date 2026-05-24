from django import forms


class PublicOrderForm(forms.Form):
    customer_name = forms.CharField(
        max_length=150,
        label="Your name",
        widget=forms.TextInput(
            attrs={
                "placeholder": "Your full name",
            }
        ),
    )
    customer_email = forms.EmailField(
        label="Email address",
        widget=forms.EmailInput(
            attrs={
                "placeholder": "you@example.com",
            }
        ),
    )
    customer_phone = forms.CharField(
        max_length=50,
        required=False,
        label="Phone / WhatsApp",
        widget=forms.TextInput(
            attrs={
                "placeholder": "+60...",
                "inputmode": "tel",
            }
        ),
    )
    quantity = forms.IntegerField(
        min_value=1,
        initial=1,
        label="Quantity",
    )