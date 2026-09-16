from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib.auth.models import User
from .models import Profile
import re


class RegisterForm(UserCreationForm):
    """Enhanced registration form with personal details and phone validation."""

    first_name = forms.CharField(
        max_length=50,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control auth-input',
            'placeholder': 'First Name',
        })
    )

    last_name = forms.CharField(
        max_length=50,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control auth-input',
            'placeholder': 'Last Name',
        })
    )

    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'form-control auth-input',
            'placeholder': 'Email Address',
        })
    )

    phone = forms.CharField(
        max_length=15,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control auth-input',
            'placeholder': 'Mobile Number',
            'pattern': '[0-9]{10}',
        }),
        help_text='Enter 10-digit mobile number'
    )

    username = forms.CharField(
        max_length=150,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control auth-input',
            'placeholder': 'Username',
        })
    )

    password1 = forms.CharField(
        label='Password',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control auth-input',
            'placeholder': 'Password',
            'id': 'id_password1',
        })
    )

    password2 = forms.CharField(
        label='Confirm Password',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control auth-input',
            'placeholder': 'Confirm Password',
            'id': 'id_password2',
        })
    )

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'username', 'password1', 'password2']

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError('This email is already registered.')
        return email

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError('This username is already taken.')
        return username

    def clean_phone(self):
        phone = self.cleaned_data.get('phone')
        phone_digits = re.sub(r'\D', '', phone or '')

        if len(phone_digits) != 10:
            raise forms.ValidationError('Mobile number must be 10 digits.')

        if phone_digits[0] not in '6789':
            raise forms.ValidationError('Invalid mobile number format.')

        return phone_digits

    def clean_first_name(self):
        first_name = self.cleaned_data.get('first_name')
        if not first_name or not first_name.replace(' ', '').isalpha():
            raise forms.ValidationError('First name must contain only letters.')
        return first_name

    def clean_last_name(self):
        last_name = self.cleaned_data.get('last_name')
        if not last_name or not last_name.replace(' ', '').isalpha():
            raise forms.ValidationError('Last name must contain only letters.')
        return last_name

    def save(self, commit=True):
        user = super().save(commit=False)

        if commit:
            user.save()
            profile, _ = Profile.objects.get_or_create(user=user)
            profile.phone = self.cleaned_data.get('phone')
            profile.save()

        return user


class EmailOrUsernameAuthenticationForm(AuthenticationForm):
    """Allow login using either email or username."""

    username = forms.CharField(
        max_length=254,
        widget=forms.TextInput(attrs={
            'class': 'form-control auth-input',
            'placeholder': 'Email or Username',
            'autocomplete': 'username',
        })
    )

    password = forms.CharField(
        label='Password',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control auth-input',
            'placeholder': 'Password',
            'autocomplete': 'current-password',
            'id': 'id_password',
        })
    )


class ProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ['phone', 'address', 'city', 'state', 'country', 'postal_code', 'profile_image']
        widgets = {
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'city': forms.TextInput(attrs={'class': 'form-control'}),
            'state': forms.TextInput(attrs={'class': 'form-control'}),
            'country': forms.TextInput(attrs={'class': 'form-control'}),
            'postal_code': forms.TextInput(attrs={'class': 'form-control'}),
            'profile_image': forms.FileInput(attrs={'class': 'form-control'}),
        }

    def clean_phone(self):
        phone = (self.cleaned_data.get('phone') or '').strip()
        if not phone:
            return phone

        phone_digits = re.sub(r'\D', '', phone)
        if len(phone_digits) != 10 or phone_digits[0] not in '6789':
            raise forms.ValidationError('Phone number must be a valid 10-digit mobile number.')

        return phone_digits

    def clean_address(self):
        address = (self.cleaned_data.get('address') or '').strip()
        if address and len(address) < 10:
            raise forms.ValidationError('Please enter a complete address.')
        return address

    def clean_city(self):
        city = (self.cleaned_data.get('city') or '').strip()
        if city and len(city) < 3:
            raise forms.ValidationError('City name is too short.')
        return city

    def clean_state(self):
        state = (self.cleaned_data.get('state') or '').strip()
        if state and len(state) < 3:
            raise forms.ValidationError('State name is too short.')
        return state

    def clean_country(self):
        country = (self.cleaned_data.get('country') or '').strip()
        if country and len(country) < 3:
            raise forms.ValidationError('Country name is too short.')
        return country

    def clean_postal_code(self):
        postal = (self.cleaned_data.get('postal_code') or '').strip()
        if postal and (not postal.isdigit() or len(postal) != 6):
            raise forms.ValidationError('Postal code must be exactly 6 digits.')
        return postal