from django.shortcuts import render, HttpResponse
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.template import RequestContext
from django.contrib.auth.models import User
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views import generic

from .forms import *
from .models import Customer, Book


# Create your views here.


def index(request):
    context = {}
    if request.user.is_authenticated:
        context['login_status'] = f'You are logged in as {request.user.username}'
    return render(request, 'index.html', context=context)


@login_required(login_url='accounts/login/')
def my_account(request):
    print(request.user)
    return render(request, 'my_account.html')


# def login(request):
#     if request.method == 'POST':
#         form = LoginForm(request.POST)
#         if form.is_valid():
#             username = form.cleaned_data['username']
#             password = form.cleaned_data['password']
#             try:
#                 customer = Customer.objects.get(username=username)
#                 # wrong password
#                 if customer.password != password:
#                     return show_error(request, "Wrong credentials, please try again", 'login')
#                 return render(request, 'my_account.html')
#             except Customer.DoesNotExist:
#                 # customer does not exist
#                 return show_error(request, "Wrong credentials, please try again", 'login')
#         else:
#             return HttpResponse('error')
#     else:
#         form = LoginForm()
#         context = {'form': form}
#         return render(request, 'login.html', context=context)


def sign_up(request):
    blank_form = SignUpForm()
    blank_context = {'form': blank_form}

    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            try:
                Customer.objects.get(username=form.cleaned_data['username'])
                # username already exists
                messages.info(request, 'User name is already taken, please choose another one')
                return render(request, 'sign_up.html', context=blank_context)
            except Customer.DoesNotExist:
                # good username, can register
                data = form.cleaned_data
                new_customer = Customer.objects.create_user(
                    username=data['username'],
                    password=data['password'],
                    first_name=data['first_name'],
                    last_name=data['last_name'],
                    address=data['address'],
                    phone_number=data['phone_number']
                )
                new_customer.save()
                context = {'status': 'Signed up successfully!'}
                return render(request, 'my_account.html', context=context)
        else:
            messages.error(request, 'Error: Unknown error, please refresh the page')
            return render(request, 'sign_up.html', context=blank_context)
    else:
        return render(request, 'sign_up.html', context=blank_context)


# def show_error(request, description, previous_page):
#     context = {'description': description, 'link': previous_page}
#     return render(request, 'show_error.html', context=context)


def book_search(request):
    blank_form = BookSearchForm()
    blank_context = {'form': blank_form}

    if request.method == 'POST':
        form = BookSearchForm(request.POST)
        if form.is_valid():
            # good search
            return book_search_result(request, form)
        else:
            # errors
            messages.error(request, "Error:")
            for _, error in form.errors.items():
                messages.error(request, error)
            return render(request, 'book_search.html', context=blank_context)
    else:
        return render(request, 'book_search.html', context=blank_context)


def book_search_result(request, form=None):
    if form is not None:
        data = form.cleaned_data
        order = data['sort_by']
        for key, value in data.items():
            if value == '':
                data.pop(key)
        result = Book.objects.filter(**data)
        context = {'book_results': form}
