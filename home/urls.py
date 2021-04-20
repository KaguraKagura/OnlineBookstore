from django.urls import path, include
from django.contrib.auth import views as auth_views

from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('accounts/', include('django.contrib.auth.urls')),
    path('accounts/profile', views.my_account, name='my_account'),
    path('sign_up', views.sign_up, name='sign_up'),
    path('book_search', views.book_search, name='book_search'),
    path('book/<str:isbn_str>', views.book_detail, name='book_detail'),
    path('shopping_cart', views.shopping_cart, name='shopping_cart')
    # path('book_search', views.BookSearchResultView.as_view(), name='book_search'),

]
