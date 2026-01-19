from django.urls import path
from .views import patients_home, dashboard_view



urlpatterns = [
    path('', dashboard_view, name='patients'),  # now /dashboard/ renders dashboard
    path('patients/', patients_home, name='patients'),
    
]











