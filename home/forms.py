from django import forms
from django.core.exceptions import ValidationError


class LoginForm(forms.Form):
    username = forms.CharField(required=True, max_length=30)
    password = forms.CharField(required=True, max_length=30)


class SignUpForm(forms.Form):
    username = forms.CharField(max_length=30)
    password = forms.CharField(max_length=30, widget=forms.PasswordInput)
    first_name = forms.CharField(max_length=30)
    last_name = forms.CharField(max_length=30)
    address = forms.CharField(max_length=100)
    phone_number = forms.CharField(max_length=10)

