from .views import register_User, login_user, user_dashboard, logout_user
from django.urls import path

urlpatterns = [
    path('register/', register_User, name='register_User'),
    path('login/', login_user, name='login_user'),
    path('logout/', logout_user, name='logout_user'),
    path('dashboard/', user_dashboard, name='user_dashboard'),
]