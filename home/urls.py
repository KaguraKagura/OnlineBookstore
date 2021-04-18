from django.urls import path, include
from django.contrib.auth import views as auth_views

from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('accounts/', include('django.contrib.auth.urls')),
    # path('accounts/login/', auth_views.LoginView.as_view()),
    path('sign_up', views.sign_up, name='sign_up'),
    path('my_account', views.my_account, name='my_account'),
    path('book_search', views.book_search, name='book_search'),

]
