from django.shortcuts import render

# Create your views here.
from .models import Patient

from django.contrib.auth.decorators import login_required





@login_required
def patients_home(request):
    # Get all patients from the database
    patients = Patient.objects.all()   
    return render(request, 'patients/patients.html', {'patients': patients})


@login_required
def dashboard_view(request):
    # You can pass patient/doctor data here if needed
    return render(request, 'patients/dashboard.html')


