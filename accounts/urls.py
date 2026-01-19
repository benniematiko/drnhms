from django.urls import path
from django.contrib.auth.views import LoginView
from .views import register, logout_view  # ✅ Correct import




urlpatterns = [
    path('login/', LoginView.as_view(template_name='accounts/login.html'), name='login'),
     path('logout/', logout_view, name='logout'),  # ✅ Change logout_View to logout_view   
    path('register/', register, name='register'),   

]
