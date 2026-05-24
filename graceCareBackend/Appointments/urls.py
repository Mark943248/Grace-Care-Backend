from .views import book_appointment, get_doctors_appointments, get_users_appointments
from django.urls import path

urlpatterns = [
    path('book/', book_appointment, name='book_appointment'),
    path('doctor-appointments/', get_doctors_appointments, name='get_doctors_appointments'),
    path('user-appointments/', get_users_appointments, name='get_users_appointments'),
]