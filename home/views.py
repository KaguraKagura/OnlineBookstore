from django import views
from django.shortcuts import render, HttpResponse, redirect
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import Http404
from django.db import transaction
from django.db.models import Q, F, Sum, Avg
from django.forms.models import model_to_dict
from django.utils.safestring import mark_safe
from django.views import generic
from django.views.generic import RedirectView
from django.template import RequestContext
from django.contrib.auth.models import User
from django.contrib.auth.mixins import LoginRequiredMixin

from .forms import *
from .models import *


# Create your views here.


def index(request):
    most_purchased_books = Book.objects.values('isbn', 'title', 'price').distinct() \
        .annotate(total_quantity=Sum('bookinorder__count')).order_by('-total_quantity')
    recommended_books = Book.objects.all().values('isbn', 'title', 'price')[:10]
    context = {'most_purchased_books': most_purchased_books,
               'recommended_books': recommended_books}
    return render(request, 'index.html', context=context)


@method_decorator(login_required(login_url='login'), name='dispatch')
class MyAccountView(views.View):
    def get(self, request, *args, **kwargs):
        customer = Customer.objects.get(username=self.request.user.username)
        comments = Comment.objects.filter(username=customer)
        trusts = TrustedCustomer.objects.filter(username=customer)
        untrusts = UntrustedCustomer.objects.filter(username=customer)
        context = {
            'customer': customer,
            'comments': comments,
            'trusts': trusts,
            'untrusts': untrusts,
        }
        return render(request, 'my_account.html', context=context)

    def post(self, request, *args, **kwargs):
        current_customer = Customer.objects.get(username=request.user.username)
        if 'trust' in request.POST:
            target_customer = Customer.objects.get(username=request.POST.get('trust'))
            change_customer_trust_status(current_customer, target_customer, 'trust')
            messages.info(request, mark_safe(f'You have successfully trusted "{target_customer}"'))
        elif 'untrust' in request.POST:
            target_customer = Customer.objects.get(username=request.POST.get('untrust'))
            change_customer_trust_status(current_customer, target_customer, 'untrust')
            messages.info(request, mark_safe(f'You have successfully untrusted "{target_customer}"'))
        return self.get(request, args, kwargs)


@login_required(login_url='login')
def my_order(request):
    customer = Customer.objects.get(username=request.user.username)
    orders = BookOrder.objects.filter(username=customer)
    orders_value = list(orders.values())
    for i in range(len(orders)):
        books_in_order = BookInOrder.objects.filter(order_number=orders[i])
        orders_value[i]['book_in_order'] = zip([book.isbn for book in books_in_order],
                                               [book.count for book in books_in_order])
    print(orders_value)
    context = {'orders': orders_value}
    return render(request, 'bookorder.html', context=context)


@login_required(login_url='login')
def shopping_cart(request):
    current_customer = Customer.objects.get(username=request.user.username)
    if request.method == 'POST':
        if 'quantity_action' in request.POST:
            action = request.POST.get('quantity_action')
            isbn = request.POST.get('isbn')
            book_in_cart = ShoppingCart.objects.get(username=current_customer, isbn=isbn)
            if action == 'decrease':
                if book_in_cart.count == 1:
                    book_in_cart.delete()
                else:
                    book_in_cart.count -= 1
                    book_in_cart.save()
            elif action == 'increase':
                book_in_cart.count += 1
                book_in_cart.save()
            return render_shopping_cart(request)
        elif 'check_out' in request.POST:
            # buy stuff
            books_in_shopping_cart = ShoppingCart.objects.filter(username=current_customer) \
                .values('isbn', 'count', title=F('isbn__title'), price=F('isbn__price'), stock=F('isbn__stock_level'))
            quantity_too_large = False
            for book in books_in_shopping_cart:
                # stock not enough
                if book['count'] > book['stock']:
                    quantity_too_large = True
                    messages.error(request,
                                   mark_safe(f'Unable to checkout:<br>&emsp;'
                                             f'Book "{book["title"]}" has only {book["stock"]} in stock<br>'))
            if quantity_too_large:
                return render_shopping_cart(request)
            else:
                total_price = 0
                for book in books_in_shopping_cart:
                    total_price += book['price'] * book['count']
                with transaction.atomic():
                    order = BookOrder.objects.create(username=current_customer, total_price=total_price)
                    for book in books_in_shopping_cart:
                        book_in_order = BookInOrder.objects.create(order_number=order,
                                                                   isbn=Book.objects.get(isbn=book['isbn']),
                                                                   count=book['count'])
                        book_in_stock = Book.objects.get(isbn=book['isbn'])
                        book_in_stock.stock_level -= book['count']
                        book_in_order.save()
                        book_in_stock.save()
                    ShoppingCart.objects.filter(username=current_customer).delete()
                messages.info(request, mark_safe('Order placed successfully! You can view it in "My Order"<br>'))
                return render_shopping_cart(request)
    else:
        return render_shopping_cart(request)


# helper
def render_shopping_cart(request):
    current_customer = Customer.objects.get(username=request.user.username)
    books_in_shopping_cart = ShoppingCart.objects.filter(username=current_customer) \
        .values('isbn', 'count', title=F('isbn__title'), price=F('isbn__price'))
    context = {
        'books_in_shopping_cart': books_in_shopping_cart,
        'total_price': 0,
    }
    if books_in_shopping_cart.exists():
        for book in books_in_shopping_cart:
            context['total_price'] += book['price'] * book['count']
    return render(request, 'shopping_cart.html', context=context)


def sign_up(request):
    blank_form = SignUpForm()
    blank_context = {'form': blank_form}

    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            try:
                Customer.objects.get(username=form.cleaned_data['username'])
                # username already exists
                messages.info(request, 'User name is already taken, please choose another one<br>')
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
                    phone_number=data['phone_number'])
                new_customer.save()
                messages.info(request, mark_safe('Signed up successfully! You can login now<br>'))
                return render(request, 'sign_up.html', context=blank_context)
        else:
            messages.error(request, 'Error: Unknown error, please refresh the page<br>')
            return render(request, 'sign_up.html', context=blank_context)
    else:
        return render(request, 'sign_up.html', context=blank_context)


def book_search(request):
    blank_form = BookSearchForm()
    blank_context = {'form': blank_form}

    if request.method == 'POST':
        form = BookSearchForm(request.POST)
        if form.is_valid():
            # good search
            return render_book_search_result(request, form)
        else:
            # errors
            messages.error(request, "Error:")
            for _, error in form.errors.items():
                messages.error(request, error)
            return render(request, 'book_search.html', context=blank_context)
    else:
        return render(request, 'book_search.html', context=blank_context)


# helper
def render_book_search_result(request, form):
    data = form.cleaned_data
    # clean data for query
    order_by = ''
    author = ''
    to_pop = []
    for key, value in data.items():
        if key == 'sort_by':
            order_by = value
            to_pop.append(key)
        elif key == 'author':
            author = value
            to_pop.append(key)
        elif value == '':
            to_pop.append(key)
    [data.pop(key) for key in to_pop]
    if author != '':
        data['author__first_name'], data['author__last_name'] = author.split('_')
    context = {'order_by': order_by}
    # start query
    if order_by != '':
        if order_by == form.SORT_CHOICE['publication_date']:
            result = Book.objects.filter(**data).order_by('publication_date')
        elif order_by == form.SORT_CHOICE['score']:
            result = Book.objects.filter(**data) \
                .values('title', 'isbn', 'publisher', 'author__first_name', 'author__last_name', 'subject', 'keywords',
                        'language', 'price') \
                .annotate(avg_score=Avg('comment__score')).order_by('avg_score')
        elif order_by == form.SORT_CHOICE['trusted_score']:
            if request.user.is_authenticated:
                result = Book.objects.filter(**data) \
                    .values('title', 'isbn', 'publisher', 'author__first_name', 'author__last_name', 'subject',
                            'keywords', 'language', 'price') \
                    .annotate(avg_score=Avg('comment__score')).order_by('avg_score')
                context['book_results'] = result
                return render(request, 'book_search_result.html', context=context)
            else:
                # if customer is not logged in, then cannot sort by trusted customer
                messages.info(request, mark_safe(
                    f'You are not logged in, thus you cannot Sort by "{form.SORT_CHOICE["trusted_score"]}"<br>'))
                context.pop('order_by')
                context['form'] = BookSearchForm()
            return render(request, 'book_search.html', context=context)
        else:
            return HttpResponse("Error")
    else:
        if author != '':
            result = Book.objects.filter(**data) \
                .values('title', 'isbn', 'publisher', 'author__first_name', 'author__last_name',
                        'subject', 'keywords', 'language', 'price')
        else:
            result = Book.objects.filter(**data) \
                .values('title', 'isbn', 'publisher', 'subject', 'keywords', 'language', 'price')
        context.pop('order_by')
    context['book_results'] = result
    return render(request, 'book_search_result.html', context=context)


def book_detail(request, isbn_str):
    if request.method == 'POST':
        if request.user.is_authenticated:
            current_customer = Customer.objects.get(username=request.user.username)
            # Add to shopping cart clicked
            if 'add_to_shopping_cart' in request.POST:
                try:
                    # book added before, increase the count by 1
                    book_in_cart = ShoppingCart.objects.get(username=current_customer,
                                                            isbn=isbn_str)
                    book_in_cart.count += 1
                    book_in_cart.save()
                    return redirect(shopping_cart)
                except ShoppingCart.DoesNotExist:
                    # book first time added, count is 1
                    shopping_cart_item = ShoppingCart.objects.create(username=current_customer,
                                                                     isbn=Book.objects.get(isbn=isbn_str),
                                                                     count=1)
                    shopping_cart_item.save()
                    return redirect(shopping_cart)
            # Submit comment clicked
            elif 'comment_textarea' in request.POST:
                if current_customer.banned is True:
                    messages.error(request, mark_safe("You are banned and cannot write a commented<br>"))
                    return render_book_detail(request, isbn_str)
                try:
                    # current user already commented
                    Comment.objects.get(username=current_customer, isbn=isbn_str)
                    messages.error(request, mark_safe(
                        "One comment per user per book -- You have already commented on this book<br>"))
                    return render_book_detail(request, isbn_str)
                except Comment.DoesNotExist:
                    # current user has never commented
                    new_comment = Comment.objects.create(username=current_customer,
                                                         isbn=Book.objects.get(isbn=isbn_str),
                                                         score=request.POST.get('scores'),
                                                         comment_text=request.POST.get('comment_textarea'))
                    new_comment.save()
                    messages.info(request, mark_safe("Your comment is successfully recorded<br>"))
                    return render_book_detail(request, isbn_str)
            else:
                try:
                    comment = Comment.objects.get(id=request.POST.get('comment_id'))
                except Comment.DoesNotExist:
                    return HttpResponse(f'Unknown error in {book_detail.__name__}, please refresh and try again')

                if comment.username == current_customer:
                    messages.error(request,
                                   mark_safe('You cannot rate your own comment! <br>'))
                    return render_book_detail(request, isbn_str)
                if 'very_useful' in request.POST:
                    comment.very_useful_count += 1
                    comment.save()
                    return render_book_detail(request, isbn_str)
                elif 'useful' in request.POST:
                    comment.useful_count += 1
                    comment.save()
                    return render_book_detail(request, isbn_str)
                elif 'useless' in request.POST:
                    comment.useless_count += 1
                    comment.save()
                    return render_book_detail(request, isbn_str)
                elif 'trust' in request.POST:
                    change_customer_trust_status(current_customer, comment.username, 'trust')
                    messages.info(request, mark_safe(f'You have successfully trusted "{comment.username}"'))
                    return render_book_detail(request, isbn_str)
                elif 'untrust' in request.POST:
                    change_customer_trust_status(current_customer, comment.username, 'untrust')
                    messages.info(request, mark_safe(f'You have successfully untrusted "{comment.username}"'))
                    return render_book_detail(request, isbn_str)
    else:
        return render_book_detail(request, isbn_str)


# helper
def change_customer_trust_status(current_customer, target_customer, action):
    with transaction.atomic():
        if action == 'trust':
            TrustedCustomer.objects.get_or_create(username=current_customer,
                                                  trusted_username=target_customer)
            try:
                untrust = UntrustedCustomer.objects.get(username=current_customer,
                                                        untrusted_username=target_customer)
                untrust.delete()
            except UntrustedCustomer.DoesNotExist:
                pass
        elif action == 'untrust':
            UntrustedCustomer.objects.get_or_create(username=current_customer,
                                                    untrusted_username=target_customer)
            try:
                trust = TrustedCustomer.objects.get(username=current_customer,
                                                    trusted_username=target_customer)
                trust.delete()
            except TrustedCustomer.DoesNotExist:
                pass


# helper
def render_book_detail(request, isbn_str):
    try:
        book = Book.objects.get(isbn=isbn_str)
    except Book.DoesNotExist:
        raise Http404('ISBN does not exist')

    authors = Author.objects.filter(isbn=isbn_str)
    comments = Comment.objects.filter(isbn=isbn_str)
    context = {'book': book,
               'comments': comments,
               'authors': authors,
               'book_dict': model_to_dict(book), }

    if request.user.is_authenticated:
        current_customer = Customer.objects.get(username=request.user.username)
        trust_status = {}
        for comment in comments:
            if comment.username == current_customer:
                trust_status[comment.id] = 'self'
                continue
            try:
                TrustedCustomer.objects.get(username=current_customer, trusted_username=comment.username)
                trust_status[comment.id] = 'trust'
                continue
            except TrustedCustomer.DoesNotExist:
                trust_status[comment.id] = ''
            try:
                UntrustedCustomer.objects.get(username=current_customer, untrusted_username=comment.username)
                trust_status[comment.id] = 'untrust'
                continue
            except UntrustedCustomer.DoesNotExist:
                trust_status[comment.id] = ''
        context['trust_status'] = trust_status,
    return render(request, 'book_detail.html', context=context)


@login_required(login_url='login')
def ask_a_question(request):
    current_customer = Customer.objects.get(username=request.user.username)
    form = CustomerQuestionForm(request.POST)
    if request.method == 'POST':
        if form.is_valid():
            data = form.cleaned_data
            question = Question(username=current_customer, question=data['question'])
            question.save()
            messages.info(request,
                          mark_safe("Your question has been recorded, check back for an answer from our managers"))
            return render_ask_a_question(request)
        else:
            return HttpResponse(f'Unknown error, please refresh and try again')

    else:
        return render_ask_a_question(request)


# helper
def render_ask_a_question(request):
    current_customer = Customer.objects.get(username=request.user.username)
    previous_questions = Question.objects.filter(username=current_customer)
    context = {'form': CustomerQuestionForm(),
               'previous_questions': previous_questions}
    return render(request, 'customer_question.html', context=context)
