from django.shortcuts import render

# Create your views here.


from .models import Doctor
from django.contrib.auth.decorators import login_required



@login_required
def doctors_home(request):
    # Get all doctors from the database
    doctors = Doctor.objects.all()   
    return render(request, 'doctors/doctors.html', {'doctors': doctors})




