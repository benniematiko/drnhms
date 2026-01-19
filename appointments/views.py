from django.shortcuts import render

# Create your views here.


from .models import Appointment
from django.contrib.auth.decorators import login_required

@login_required
def appointments_home(request):
    # Get all appointments from the database
    appointments = Appointment.objects.all()   
    return render(request, 'appointments/appointments.html', {'appointments': appointments})



