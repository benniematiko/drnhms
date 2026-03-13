from django.urls import path
# from .views import pharmacy_home, generatebill, medicinesearch
from . import views

urlpatterns = [
    # Main pages
    
    path('pharmacy/', views.pharmacy_home, name='pharmacy'),
    path('pharmacy/generatebill/', views.generatebill, name='generatebill'),
    path('pharmacy/medicinesearch/', views.medicinesearch, name='medicinesearch'),
    path('pharmacy/medicinepurchaselist/', views.medicinepurchaselist, name='medicinepurchaselist'),
    path('pharmacy/purchasemedicine/', views.purchasemedicine, name='purchasemedicine'),



    # ✅ NEW: Add patient from generate bill to enable saving of from the add-patient modal
    path('pharmacy/add-patient/', views.add_patient_from_bill, name='add_patient_from_bill'),
    path('pharmacy/add-patient-ajax/', views.add_patient_ajax, name='add_patient_ajax'),  # Optional AJAX version

    


    # API endpoints - these MUST have the pharmacy/ prefix
    path('get-medicines-by-category/<int:category_id>/', views.get_medicines_by_category, name='get_medicines_by_category'),  # NEW
    path('get-batches-by-medicine/',views.get_batches_by_medicine,name='get_batches_by_medicine'),
    path('get-patients/',views.get_patients,name='get_patients'),
    path('save-medicine-purchase/',views.save_medicine_purchase,name='save_medicine_purchase'),
       
    
    path('save-purchase/', views.save_drug_purchase, name='save_purchase'),
    # ... save medicine from purchasemedicine.html page urls
    path('purchasemedicine/', views.purchase_medicine_form, name='purchasemedicine'),  
    

    
]

  


       
    









