from django.urls import path


from .views import dashboard_view, get_dashboard_totals  # Import the new view

urlpatterns = [
    path('', dashboard_view, name='dashboard'),  # patients/ → dashboard
    path('api/totals/', get_dashboard_totals, name='dashboard_totals'),  # API endpoint for auto-refresh

]







