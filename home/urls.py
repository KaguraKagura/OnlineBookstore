from django.urls import path, include
from django.contrib.auth import views as auth_views

from . import views

urlpatterns = [
    path('', views.index, name='home'),
    path('book_search', views.book_search, name='book_search'),
    path('shopping_cart', views.shopping_cart, name='shopping_cart'),
    path('accounts/my_account', views.MyAccountView.as_view(), name='my_account'),
    path('my_order', views.my_order, name='my_order'),
    path('ask_a_question', views.ask_a_question, name='ask_a_question'),
    path('accounts/', include('django.contrib.auth.urls')),
    path('sign_up', views.sign_up, name='sign_up'),
    path('book/<str:isbn_str>', views.book_detail, name='book_detail'),
    # path('book_search', views.BookSearchResultView.as_view(), name='book_search'),

]
