from datetime import datetime, timedelta

from django import views
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import login_required
from django.db import connection
from django.db.models import Sum, Count
from django.shortcuts import redirect
from django.utils.decorators import method_decorator

from .utils import *


# Create your views here.

# displays recommended books on the index page
def index(request):
    most_purchased_books = Book.objects.values('isbn', 'title', 'price') \
                               .annotate(total_quantity=Sum('bookinorder__count')).order_by('-total_quantity')[:10]
    if request.user.is_authenticated and not request.user.is_superuser:
        current_customer = Customer.objects.get(username=request.user.username)
        recommended_books = Book.objects.exclude(bookinorder__order_number__username=current_customer) \
                                .values('isbn', 'title', 'price')[:10]
    else:
        recommended_books = Book.objects.values('isbn', 'title', 'price')[:10]
    context = {'most_purchased_books': most_purchased_books,
               'recommended_books': recommended_books}
    return render(request, 'index.html', context=context)


# get and clean search criteria
def book_search(request):
    blank_form = BookSearchForm()
    blank_context = {'form': blank_form}

    if request.method == 'POST':
        form = BookSearchForm(request.POST)
        # good search
        if form.is_valid():
            return render_book_search_result(request, form)
        # errors
        else:
            messages.error(request, "Error:")
            for _, error in form.errors.items():
                messages.error(request, error)
            return render(request, 'book_search.html', context=blank_context)
    else:
        return render(request, 'book_search.html', context=blank_context)


@login_required(login_url='login')
def shopping_cart(request):
    current_customer = Customer.objects.get(username=request.user.username)
    if request.method == 'POST':
        # increase or decrease item count in the shopping cart
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
        # checkout
        elif 'check_out' in request.POST:
            books_in_shopping_cart = ShoppingCart.objects.filter(username=current_customer) \
                .values('isbn', 'count', title=F('isbn__title'), price=F('isbn__price'), stock=F('isbn__stock_level'))
            quantity_too_large = False
            # check if stock is enough
            for book in books_in_shopping_cart:
                if book['count'] > book['stock']:
                    quantity_too_large = True
                    messages.error(request, mark_safe(f'Unable to checkout:<br>&emsp;'
                                                      f'Book "{book["title"]}" has only {book["stock"]} in stock<br>'))
            if quantity_too_large:
                return render_shopping_cart(request)
            else:
                total_price = 0
                for book in books_in_shopping_cart:
                    total_price += book['price'] * book['count']
                # atomically create an order and decrease stock
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


@method_decorator(login_required(login_url='login'), name='dispatch')
class MyAccountView(views.View):
    def get(self, request, *args, **kwargs):
        # displays customer's own info, comments, and trusted/untrusted customers
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
        # trust or untrust a customer on MyAccount page
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
    # get all orders of a customer
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
def my_question(request):
    # displays customer's questions and answers
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


# creates a new customer
def sign_up(request):
    blank_form = SignUpForm()
    blank_context = {'form': blank_form}
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            try:
                # if customer query succeeds without exception, it means username already exists
                Customer.objects.get(username=form.cleaned_data['username'])
                messages.info(request, 'User name is already taken, please choose another one<br>')
                return render(request, 'sign_up.html', context=blank_context)
            except Customer.DoesNotExist:
                # available username, can sign up
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
            # invalid fields entered
            messages.error(request, mark_safe('Invalid item entered, please check again<br>'))
            return render(request, 'sign_up.html', context=blank_context)
    else:
        return render(request, 'sign_up.html', context=blank_context)


# special search page for degrees of separation
class DegreeOfSeparationSearchView(views.View):
    form = DegreeOfSeparationSearchForm()
    context = {'form': form}

    def get(self, request, *args, **kwargs):
        return render(request, 'degree_of_separation_search.html', context=self.context)

    def post(self, request, *args, **kwargs):
        author = request.POST.get('author')
        firstname, lastname = author.split('_')
        degree = int(request.POST.get('degree_of_separation'))
        context = {'first_name_searched_on': firstname,
                   'last_name_searched_on': lastname}
        # raw SQL for authors with degree 1 relationship
        with connection.cursor() as cursor:
            cursor.execute('SELECT A2.first_name, A2.last_name '
                           'FROM home_author A1 join home_author A2 on A1.isbn_id = A2.isbn_id '
                           'WHERE A1.first_name = %s AND A1.last_name = %s '
                           'AND A2.first_name != %s AND A2.last_name != %s',
                           [firstname, lastname, firstname, lastname])
            raw_separated_authors = cursor.fetchall()
        if degree == 1:
            context['degree'] = 1
        elif degree == 2:
            # helper to see if there exists a degree 1 relationship
            def degree1Exists(fn, ln, fn_from_search, ln_from_search):
                with connection.cursor() as c:
                    c.execute('SELECT A2.first_name, A2.last_name '
                              'FROM home_author A1 join home_author A2 on A1.isbn_id = A2.isbn_id '
                              'WHERE A1.first_name = %s AND A1.last_name = %s '
                              'AND A2.first_name != %s AND A2.last_name != %s '
                              'AND A2.first_name != %s AND A2.last_name != %s',
                              [fn, ln, fn, ln, fn_from_search, ln_from_search])
                    result = c.fetchall()
                    return result

            temp_raw_author = []
            # for degree 2 search, only keep authors who have no degree 1 relationship among each other
            [temp_raw_author.append(raw_author) for raw_author in raw_separated_authors
             if not degree1Exists(raw_author[0], raw_author[1], firstname, lastname)]
            raw_separated_authors = temp_raw_author
            context['degree'] = 2
        # turn raw result into a dict with meaningful keys
        context['authors'] = [dict(zip(['first_name', 'last_name'], raw_author))
                              for raw_author in raw_separated_authors]
        # get the books the target authors write
        for author in context['authors']:
            author['books'] = Book.objects.filter(author__first_name=author['first_name'],
                                                  author__last_name=author['last_name']).order_by('title')
        return render(request, 'degree_of_separation_search_result.html', context=context)


def book_detail(request, isbn_str):
    if request.method == 'POST':
        if request.user.is_authenticated:
            current_customer = Customer.objects.get(username=request.user.username)
            # add to shopping cart
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
            # comment submitted
            elif 'comment_textarea' in request.POST:
                # banned customer
                if current_customer.banned is True:
                    messages.error(request, mark_safe("You are banned and cannot write a commented<br>"))
                    return render_book_detail(request, isbn_str)
                try:
                    # current user already commented, cannot comment again
                    Comment.objects.get(username=current_customer, isbn=isbn_str)
                    messages.error(request, mark_safe(
                        "One comment per user per book -- You have already commented on this book<br>"))
                    return render_book_detail(request, isbn_str)
                except Comment.DoesNotExist:
                    # current user has never commented, can proceed
                    new_comment = Comment.objects.create(username=current_customer,
                                                         isbn=Book.objects.get(isbn=isbn_str),
                                                         score=request.POST.get('scores'),
                                                         comment_text=request.POST.get('comment_textarea'))
                    new_comment.save()
                    messages.info(request, mark_safe("Your comment is successfully recorded<br>"))
                    return render_book_detail(request, isbn_str)
            # comment rated
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
                    comment.usefulness_score = \
                        (comment.very_useful_count * 2 + comment.useful_count + comment.useless_count * -1) / 3.0
                    comment.save()
                    return render_book_detail(request, isbn_str)
                elif 'useful' in request.POST:
                    comment.useful_count += 1
                    comment.usefulness_score = \
                        (comment.very_useful_count + comment.useful_count + comment.useless_count) / 3.0
                    comment.save()
                    return render_book_detail(request, isbn_str)
                elif 'useless' in request.POST:
                    comment.useless_count += 1
                    comment.usefulness_score = \
                        (comment.very_useful_count + comment.useful_count + comment.useless_count) / 3.0
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


# manager only page for customer stat
@method_decorator(staff_member_required(login_url='admin:login'), name='dispatch')
class AdminUserStatView(views.View):
    def get(self, request, *args, **kwargs):
        return render(request, 'admin_user_stat_view.html')

    def post(self, request, *args, **kwargs):
        try:
            number = int(request.POST.get('number'))
            if number <= 0:
                return HttpResponse('Please enter a positive integer')
        except ValueError:
            return HttpResponse('Please enter a positive integer')
        context = {}
        if 'top_trusted' in request.POST:
            customers = (Customer.objects.values(
                'username', 'first_name', 'last_name', 'address', 'phone_number', 'banned')) \
                            .annotate(Count('t_trusted_username')).order_by('-t_trusted_username__count')[:number]
            context['customers'] = customers
            context['trust'] = 1
        elif 'top_useful' in request.POST:
            customers = Customer.objects.values(
                'username', 'first_name', 'last_name', 'address', 'phone_number', 'banned') \
                            .annotate(usefulness_score=Avg('comment__usefulness_score')) \
                            .order_by('-usefulness_score')[:number]
            context['customers'] = customers
            context['useful'] = 1
        return render(request, 'admin_user_stat_view.html', context=context)


# manager only page for book stat
@method_decorator(staff_member_required(login_url='admin:login'), name='dispatch')
class AdminBookStatView(views.View):
    def get(self, request, *args, **kwargs):
        return render(request, 'admin_book_stat_view.html')

    def post(self, request, *args, **kwargs):
        try:
            number = int(request.POST.get('number'))
            if number <= 0:
                return HttpResponse('Please enter a positive integer')
        except ValueError:
            return HttpResponse('Please enter a positive integer')
        context = {}
        # recent quarter
        one_quarter_ago = datetime.now() - timedelta(days=90)
        print(one_quarter_ago)
        if 'top_books' in request.POST:
            books = BookInOrder.objects.filter(order_number__order_time__gt=one_quarter_ago) \
                        .values('isbn', 'isbn__title').annotate(count=Sum('count')) \
                        .order_by('-count')[:number]
            context['results'] = books
            context['result_type'] = 'books'
        elif 'top_authors' in request.POST:
            authors = Book.objects.filter(bookinorder__order_number__order_time__gt=one_quarter_ago) \
                          .values('author__first_name', 'author__last_name') \
                          .annotate(count=Sum('bookinorder__count')) \
                          .order_by('-count')[:number]
            print(authors)
            context['results'] = authors
            context['result_type'] = 'authors'
        elif 'top_publishers' in request.POST:
            publishers = Book.objects.filter(bookinorder__order_number__order_time__gt=one_quarter_ago) \
                             .values('publisher').annotate(count=Sum('bookinorder__count')) \
                             .order_by('-count')[:number]
            print(publishers)
            context['results'] = publishers
            context['result_type'] = 'publishers'
        return render(request, 'admin_book_stat_view.html', context=context)
