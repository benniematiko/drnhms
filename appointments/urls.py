from django.urls import path
from .views import appointments_home



urlpatterns = [
   
    path('', appointments_home, name='appointments'),
]

