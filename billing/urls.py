from django.urls import path
from .views import billings_home, save_bill


# Save into database

from . import views



urlpatterns = [
   
    path('save/',views.save_bill, name='save_bill'),
    path('', billings_home, name='billings'),
]

