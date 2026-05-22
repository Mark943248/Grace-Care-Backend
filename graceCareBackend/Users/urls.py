from .views import register_User, login_user, user_dashboard
from django.urls import path

urlpatterns = [
    path('register/', register_User, name='register_User'),
    path('login/', login_user, name='login_user'),
    path('dashboard/', user_dashboard, name='user_dashboard'),
]