from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, Count
from django.http import JsonResponse

# Import your models
from billing.models import Invoice, Payment
from appointments.models import Appointment
from patients.models import Patient


@login_required
def dashboard_view(request):
    """Main dashboard view - renders the dashboard page"""
    # Pharmacy Income - sum of paid invoices containing pharmacy items
    pharmacy_income = Invoice.objects.filter(
        status='PAID',
        items__drug__isnull=False
    ).aggregate(total=Sum('net_amount'))['total'] or 0
    
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
    
    # Laboratory Income - you need to add this logic based on your data model
    laboratory_income = 0  # Replace with actual calculation
    
    # Radiology Income
    radiology_income = 0  # Replace with actual calculation
    
    # Blood Bank Income
    blood_income = 0  # Replace with actual calculation
    
    # Ambulance Income
    ambulance_income = 0  # Replace with actual calculation
    
    # General Income
    general_income = 0  # Replace with actual calculation
    
    # Expenses
    expenses = 0  # Replace with actual calculation
    
    # Total number of scheduled appointments
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
        'laboratory_income': laboratory_income,
        'radiology_income': radiology_income,
        'blood_income': blood_income,
        'ambulance_income': ambulance_income,
        'general_income': general_income,
        'expenses': expenses,
        'total_appointments': total_appointments,
        'total_patients': total_patients,
        'total_payments': total_payments,
    }
    
    return render(request, 'dashboard/dashboard.html', context)


@login_required
def get_dashboard_totals(request):
    """API endpoint to get updated dashboard totals for AJAX auto-refresh"""
    
    # Pharmacy Income
    pharmacy_income = Invoice.objects.filter(
        status='PAID',
        items__drug__isnull=False
    ).aggregate(total=Sum('net_amount'))['total'] or 0
    
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
    
    # Laboratory Income
    laboratory_income = 0  # Replace with actual calculation
    
    # Radiology Income
    radiology_income = 0  # Replace with actual calculation
    
    # Blood Bank Income
    blood_income = 0  # Replace with actual calculation
    
    # Ambulance Income
    ambulance_income = 0  # Replace with actual calculation
    
    # General Income
    general_income = 0  # Replace with actual calculation
    
    # Expenses
    expenses = 0  # Replace with actual calculation
    
    # Total appointments
    total_appointments = Appointment.objects.filter(
        status='SCHEDULED'
    ).count()
    
    # Total patients
    total_patients = Patient.objects.count()
    
    # Total payments
    total_payments = Payment.objects.aggregate(
        total=Sum('amount')
    )['total'] or 0
    
    return JsonResponse({
        'pharmacy_income': float(pharmacy_income),
        'opd_income': float(opd_income),
        'ipd_income': float(ipd_income),
        'laboratory_income': float(laboratory_income),
        'radiology_income': float(radiology_income),
        'blood_income': float(blood_income),
        'ambulance_income': float(ambulance_income),
        'general_income': float(general_income),
        'expenses': float(expenses),
        'total_appointments': total_appointments,
        'total_patients': total_patients,
        'total_payments': float(total_payments)
    })