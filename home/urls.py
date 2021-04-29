from django.urls import path, include

from . import views

urlpatterns = [
    path('', views.index, name='home'),
    path('book_search', views.book_search, name='book_search'),
    path('shopping_cart', views.shopping_cart, name='shopping_cart'),
    path('accounts/my_account', views.MyAccountView.as_view(), name='my_account'),
    path('my_order', views.my_order, name='my_order'),
    path('my_question', views.my_question, name='my_question'),
    path('accounts/', include('django.contrib.auth.urls')),
    path('sign_up', views.sign_up, name='sign_up'),
    path('book/<str:isbn_str>', views.book_detail, name='book_detail'),
    path('degree_of_separation_search', views.DegreeOfSeparationSearchView.as_view(), name='degree_of_separation_search'),
    path('admin_user_report', views.AdminUserStatView.as_view(), name='admin_user_report'),
    path('admin_book_report', views.AdminBookStatView.as_view(), name='admin_user_report'),
]
