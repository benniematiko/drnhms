from django.shortcuts import render

# Create your views here.
from django.contrib.auth.decorators import login_required

# Get totals in the dashboard page dashboard.html

from django.db.models import Sum


from django.db.models import Sum, Count
from billing.models import Invoice, Payment
from appointments.models import Appointment
from patients.models import Patient



# @login_required
# def dashboard_view(request):
#     return render(request, 'dashboard/dashboard.html') 



@login_required
def dashboard_view(request):
    # Pharmacy Income - sum of paid invoices containing pharmacy items
    pharmacy_income = Invoice.objects.filter(
        status='PAID',
        items__drug__isnull=False  # Has drug items
    ).aggregate(total=Sum('net_amount'))['total'] or 0
    
    # Alternative: Calculate from InvoiceItems directly
    # from billing.models import InvoiceItem
    # pharmacy_income = InvoiceItem.objects.filter(
    #     invoice__status='PAID'
    # ).aggregate(total=Sum('line_total'))['total'] or 0
    
    # OPD Income
    opd_income = Invoice.objects.filter(
        status='PAID',
        invoice_type='OPD'
    ).aggregate(total=Sum('net_amount'))['total'] or 0

    # IPD Income
    ipd_income = Invoice.objects.filter(
        status='PAID',
        invoice_type='IPD'
    ).aggregate(total=Sum('net_amount'))['total'] or 0
    
    # Total number of appointments
    total_appointments = Appointment.objects.filter(
        status='SCHEDULED'
    ).count()
    
    # Total patients
    total_patients = Patient.objects.count()
    
    # Total payments received
    total_payments = Payment.objects.aggregate(
        total=Sum('amount')
    )['total'] or 0
    
    context = {
        'pharmacy_income': pharmacy_income,
        'opd_income': opd_income,
        'ipd_income': ipd_income,
        'total_appointments': total_appointments,
        'total_patients': total_patients,
        'total_payments': total_payments,
    }
    
    return render(request, 'dashboard/dashboard.html', context)