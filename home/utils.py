from django.db import transaction
from django.db.models import F, Avg
from django.forms import model_to_dict
from django.http import Http404
from django.shortcuts import render, HttpResponse
from django.utils.safestring import mark_safe
from django.contrib import messages

from .models import *
from .forms import *


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


# helper
def render_ask_a_question(request):
    current_customer = Customer.objects.get(username=request.user.username)
    previous_questions = Question.objects.filter(username=current_customer)
    context = {'form': CustomerQuestionForm(),
               'previous_questions': previous_questions}
    return render(request, 'customer_question.html', context=context)
