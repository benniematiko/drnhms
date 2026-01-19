from django.urls import path
from .views import doctors_home



urlpatterns = [
   
    path('', doctors_home, name='doctors'),
   
]
