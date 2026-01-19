"""
URL configuration for nyangombe_main project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.contrib import admin
from django.urls import path, include
# from .views import home
from core.views import home
from django.views.generic import RedirectView



urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('core.urls')),   # 👈 root goes to core
    # path('', home, name='home'),   # homepage at '/' 
   
    path('dashboard/', include('dashboard.urls')),  # redirect after login
    path('accounts/', include('accounts.urls')),  # login/register/logout
    # path('', RedirectView.as_view(url='/dashboard/')),  # redirect root '/' to dashboard
    path('doctors/', include('doctors.urls')),       # doctors app ✅
    path('pharmacy/', include('pharmacy.urls')),       # pharmacy app ✅
    path('appointments/', include('appointments.urls')),       # appointments app ✅
    path('billing/', include('billing.urls')),  # or 'pharmacy.urls'
    path('payments/', include('billing.urls')),       # payments app ✅

    
     
]






















