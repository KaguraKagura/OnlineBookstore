from django import forms
from django.core.exceptions import ValidationError
from .models import Book


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


class BookSearchForm(forms.Form):
    isbn = forms.CharField(max_length=13, required=False, label='ISBN')
    title = forms.CharField(max_length=100, required=False)
    publisher = forms.CharField(max_length=100, required=False)

    subject_choices = [(i, i) for i in
                       ['---'] + list(Book.objects.values_list('subject', flat=True).order_by('subject').distinct())]
    keywords_choices = [(i, i) for i in
                        ['---'] + list(Book.objects.values_list('keywords', flat=True).order_by('keywords').distinct())]
    language_choices = [(i, i) for i in
                        ['---'] + list(Book.objects.values_list('language', flat=True).order_by('language').distinct())]
    sort_by_choices = [(i, i) for i in ['---', 'Publish Date', 'Score', 'Trusted user score']]
    subject = forms.ChoiceField(choices=subject_choices)
    keywords = forms.ChoiceField(choices=keywords_choices)
    language = forms.ChoiceField(choices=language_choices)
    sort_by = forms.ChoiceField(choices=sort_by_choices)

    def clean(self):
        super().clean()
        data = self.cleaned_data
        if data['isbn'] == '' and data['title'] == '' and data['publisher'] == '' and data['subject'] == '---' and \
                data['keywords'] == '---' and data['language'] == '---':
            raise ValidationError('Empty search', code='empty_search')
