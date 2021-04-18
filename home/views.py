from django.shortcuts import render, HttpResponse
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views import generic

from .forms import LoginForm, SignUpForm
from .models import Customer, Book


# Create your views here.


def index(request):
    return render(request, 'index.html')


@login_required
def my_account(request):
    return render(request, 'account.html')


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
#                 return render(request, 'account.html')
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
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            try:
                Customer.objects.get(username=form.cleaned_data['username'])
                # login name already exists
                return show_error(request, "Login name already taken, please choose another one", 'sign_up')
            except Customer.DoesNotExist:
                # good login name, can register
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
                return HttpResponse(new_customer)
        else:
            return HttpResponse('error')
    else:
        form = SignUpForm()
        context = {'form': form}
        return render(request, 'sign_up.html', context=context)


def show_error(request, description, previous_page):
    context = {'description': description, 'link': previous_page}
    return render(request, 'show_error.html', context=context)
