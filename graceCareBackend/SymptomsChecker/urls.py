from .views import SymptomCheckerView
from django.urls import path

urlpatterns = [
    path('SymptomChecker/', SymptomCheckerView.as_view(), name='symptom_checker'),
]