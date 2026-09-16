from django import forms
from decimal import Decimal

from .models import ContactMessage, Coupon, Review


class ReviewForm(forms.ModelForm):

    class Meta:

        model = Review

        fields = ("rating","comment",)

        widgets = {

            "rating": forms.Select(
                attrs={"class": "form-select"}
            ),

            "comment": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 4,
                    "placeholder": "Write your review..."
                }
            )

        }




class ContactForm(forms.ModelForm):

    class Meta:
        model = ContactMessage
        fields = ("full_name", "email", "subject", "message")

    full_name = forms.CharField(
        max_length=100,
        required=True,
        widget=forms.TextInput(attrs={
            "class": "form-control",
            "placeholder": "Enter your name"
        })
    )

    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            "class": "form-control",
            "placeholder": "Enter your email"
        })
    )

    subject = forms.CharField(
        max_length=150,
        required=True,
        widget=forms.TextInput(attrs={
            "class": "form-control",
            "placeholder": "Enter subject"
        })
    )

    message = forms.CharField(
        required=True,
        widget=forms.Textarea(attrs={
            "class": "form-control",
            "placeholder": "Write your message",
            "rows": 6
        })
    )


    def clean_full_name(self):

        name = self.cleaned_data["full_name"].strip()

        if len(name) < 3:
            raise forms.ValidationError(
                "Name must contain at least 3 characters."
            )

        if not all(char.isalpha() or char.isspace() for char in name):
            raise forms.ValidationError(
                "Name can contain only letters and spaces."
            )

        return name



    def clean_subject(self):

        subject = self.cleaned_data["subject"].strip()

        if len(subject) < 5:
            raise forms.ValidationError(
                "Subject must contain at least 5 characters."
            )

        return subject



    def clean_message(self):

        message = self.cleaned_data["message"].strip()

        if len(message) < 10:
            raise forms.ValidationError(
                "Message must contain at least 10 characters."
            )

        return message


class CouponForm(forms.Form):

    coupon_code = forms.CharField(
        max_length=50,
        widget=forms.TextInput(attrs={
            "class": "form-control",
            "placeholder": "Enter coupon code",
        }),
    )

    def __init__(self, *args, cart_total, **kwargs):
        super().__init__(*args, **kwargs)
        self.cart_total = cart_total

    def clean_coupon_code(self):

        code = self.cleaned_data["coupon_code"].strip().upper()

        try:

            coupon = Coupon.objects.get(
                code__iexact=code,
                active=True
            )

        except Coupon.DoesNotExist:

            raise forms.ValidationError(
                "Invalid coupon code."
            )

        if not coupon.is_valid():

            raise forms.ValidationError(
                "This coupon has expired or is not active."
            )

        if self.cart_total < coupon.minimum_amount:

            raise forms.ValidationError(
                f"Minimum order amount is ₹{coupon.minimum_amount}."
            )

        self.coupon = coupon

        return code

    def get_discount(self):

        discount = (
            self.cart_total
            * self.coupon.discount_percent
            / Decimal("100")
        )

        if self.coupon.maximum_discount:

            discount = min(
                discount,
                self.coupon.maximum_discount
            )

        return discount