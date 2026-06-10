from django import forms

from .models import PaymentProof


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


class PaymentProofForm(forms.ModelForm):
    """Form for uploading proof of payment for an order."""

    class Meta:
        model = PaymentProof
        fields = ["file", "notes"]
        widgets = {
            "file": forms.FileInput(
                attrs={
                    "accept": ".pdf,.jpg,.jpeg,.png",
                    "class": "payment-proof-input",
                }
            ),
            "notes": forms.Textarea(
                attrs={
                    "rows": 3,
                    "placeholder": "Optional: Add any notes about your payment (e.g., payment method, date, transaction ID)",
                }
            ),
        }
        labels = {
            "file": "Upload Proof of Payment",
            "notes": "Additional Details (optional)",
        }
        help_texts = {
            "file": "Upload a receipt, bank transfer screenshot, or payment confirmation (PDF, JPG, PNG)"
        }

    def clean_file(self):
        file = self.cleaned_data.get("file")
        if file:
            # Check file size (max 10MB)
            if file.size > 10 * 1024 * 1024:
                raise forms.ValidationError("File size must not exceed 10MB.")
        return file
