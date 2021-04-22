from django.shortcuts import render, HttpResponse, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import Http404
from django.db.models import F, Sum
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

# def get_queryset(self):
# request = self.request
# blank_form = BookSearchForm()
# blank_context = {'form': blank_form}
#
# if request.method == 'POST':
#     form = BookSearchForm(request.POST)
#     if form.is_valid():
#         # good search
#         return book_search_result(request, form)
#     else:
#         # errors
#         messages.error(request, "Error:")
#         for _, error in form.errors.items():
#             messages.error(request, error)
#         return render(request, 'book_search.html', context=blank_context)
# else:
#     return render(request, 'book_search.html', context=blank_context)


def index(request):
    return render(request, 'index.html')


@login_required(login_url='login')
def my_account(request):
    print(request.user)
    return render(request, 'profile.html')


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
            books_in_shopping_cart = ShoppingCart.objects.filter(
                username=current_customer).values(
                'isbn', 'count', title=F('isbn__title'), price=F('isbn__price'), stock=F('isbn__stock_level'))
            has_invalid_count = False
            for book in books_in_shopping_cart:
                if book['count'] > book['stock']:
                    has_invalid_count = True
                    messages.error(request, mark_safe(
                        f'Unable to checkout:<br>&emsp;'
                        f'Book "{book["title"]}" has only {book["stock"]} in stock, '
                        f'please adjust the quantity<br>'))
            if has_invalid_count is True:
                return render_shopping_cart(request)
            else:
                pass
            # count = BookOrder.objects.filter(isbn=isbn).values('isbn').annotate(sum_count=Sum('count'))
            # if count.exists():
            # print(count.values('sum_count'))


    else:
        return render_shopping_cart(request)


# helper
def render_shopping_cart(request):
    current_customer = Customer.objects.get(username=request.user.username)
    books_in_shopping_cart = ShoppingCart.objects.filter(
        username=current_customer).values(
        'isbn', 'count', title=F('isbn__title'), price=F('isbn__price'))
    context = {
        'books_in_shopping_cart': books_in_shopping_cart,
        'total_price': 0,
    }
    if books_in_shopping_cart.exists():
        for book in books_in_shopping_cart:
            context['total_price'] += book['price'] * book['count']
    return render(request, 'shopping_cart.html', context=context)


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
#                 return render(request, 'profile.html')
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
                    phone_number=data['phone_number']
                )
                new_customer.save()
                context = {'status': 'Signed up successfully!'}
                return render(request, 'profile.html', context=context)
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
            return book_search_result(request, form)
        else:
            # errors
            messages.error(request, "Error:")
            for _, error in form.errors.items():
                messages.error(request, error)
            return render(request, 'book_search.html', context=blank_context)
    else:
        return render(request, 'book_search.html', context=blank_context)


# helper
def book_search_result(request, form):
    data = form.cleaned_data
    order_by = data['sort_by']
    data.pop('sort_by')
    to_pop = []

    for key, value in data.items():
        if value == '':
            to_pop.append(key)
    [data.pop(key) for key in to_pop]

    context = {'order_by': order_by}
    if order_by != '':
        if order_by == form.SORT_CHOICE['publication_date']:
            result = Book.objects.filter(**data).order_by('publication_date')
        elif order_by == form.SORT_CHOICE['score']:
            return HttpResponse("NOT COMPLETED")
            # result = Book.objects.filter(comment__isbn=Book.isbn).values(
            #     'isbn').annotate(avg_score=Avg('comment__score')).order_by('avg_score')
        elif order_by == form.SORT_CHOICE['trusted_score']:
            if request.user.is_authenticated:
                # result = Book.objects.select_related('isbn').filter(
                #     comment__isbn=Book.isbn,
                #     trustedcustomer__username=request.user,
                #     trustedcustomer__trusted_username=Comment.username
                # ).values('isbn').annotate(avg_score=Avg('comment__score')).order_by('avg_score')

                # result = Book.objects.raw('SELECT title'
                #                           'FROM home_book B'
                #                           'JOIN home_comment C'
                #                           'JOIN home_trustedcustomer T '
                #                           'ON isbn = C.isbn_id AND C.username_id = T.trusted_username_id AND T.username_id = %s'
                #                           'WHERE B.isbn = %(isbn)s'
                #                           'AND B.title = %s'
                #                           'AND B.publisher = %s'
                #                           'AND B.subject = %s'
                #                           'AND B.keywords = %s'
                #                           'AND B.language = %s'
                #                           'GROUP BY isbn'
                #                           'ORDER BY AVG(score)', [1], **data)
                return HttpResponse("NOT COMPLETED")
            else:
                # not logged in cannot sort by trusted customer
                messages.info(request, mark_safe(
                    f'You are not logged in, thus you cannot Sort by "{form.SORT_CHOICE["trusted_score"]}"<br>'))
                context.pop('order_by')
                context['form'] = BookSearchForm()
            return render(request, 'book_search.html', context=context)
        else:
            return HttpResponse("Error")
    else:
        result = Book.objects.filter(**data)
    context = {'book_results': result}
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
                    messages.error(request, "You are banned and cannot write a commented<br>")
                    return render_book_detail(request, isbn_str)
                try:
                    # current user already commented
                    Comment.objects.get(username=current_customer, isbn=isbn_str)
                    messages.error(request,
                                   "One comment per user per book -- You have already commented on this book<br>")
                    return render_book_detail(request, isbn_str)
                except Comment.DoesNotExist:
                    # current user has never commented
                    new_comment = Comment.objects.create(username=current_customer,
                                                         isbn=Book.objects.get(isbn=isbn_str),
                                                         score=request.POST.get('scores'),
                                                         comment_text=request.POST.get('comment_textarea'))
                    new_comment.save()
                    return render_book_detail(request, isbn_str)
        else:
            try:
                # rated a existing comment
                comment = Comment.objects.get(id=request.POST.get('comment_id'))
                if 'very_useful' in request.POST:
                    comment.very_useful_count += 1
                elif 'useful' in request.POST:
                    comment.useful_count += 1
                elif 'useless' in request.POST:
                    comment.useless_count += 1
                comment.save()
                return render_book_detail(request, isbn_str)
            except Comment.DoesNotExist:
                return HttpResponse(f'Unknown error in {book_detail.__name__}, please refresh and try again')
    else:
        return render_book_detail(request, isbn_str)


# helper
def render_book_detail(request, isbn_str):
    try:
        authors = Author.objects.filter(isbn=isbn_str)
        book = Book.objects.get(isbn=isbn_str)
        comments = Comment.objects.filter(isbn=isbn_str)
    except Book.DoesNotExist:
        raise Http404('ISBN does not exist')

    context = {'book': book,
               'comments': comments,
               'authors': authors,
               'book_dict': model_to_dict(book),
               }
    return render(request, 'book_detail.html', context=context)
