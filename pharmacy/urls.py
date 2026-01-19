from django.urls import path
from .views import pharmacy_home, generatebill
from . import views



urlpatterns = [
    
    path('pharmacy/', pharmacy_home, name='pharmacy'),
    # path('generatebill/', generatebill_home, name='generatebill'),     

    # path('get_drugs/<int:category_id>/', views.get_drugs, name='get_drugs'),
    # path('get_drug_details/<int:drug_id>/', views.get_drug_details, name='get_drug_details'),
   
    path('get-medicines/', views.get_medicines_by_category, name='get_medicines'),  # Make sure name matches
    path('get-batches/', views.get_batches_by_medicine, name='get_batches'), 
    path('get-patients/', views.get_patients, name='get_patients'),  # Add patient name in the generate.html
    # path('pharmacy/get_doctor_view/', views.getdoctor, name='get_doctor'),
    path('pharmacy/generatebill/', views.generatebill, name='generatebill'),
]









