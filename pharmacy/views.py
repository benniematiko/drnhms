from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, F, Value, DecimalField, ExpressionWrapper, Case, When
from django.db.models.functions import Coalesce
from django.http import JsonResponse
from django.contrib import messages
from django.db import transaction
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

from billing.models import Invoice, InvoiceItem, Payment
from .models import DrugCategory, Drug
from doctors.models import Doctor
from patients.models import Patient

from decimal import Decimal
import json
import uuid
from datetime import datetime


@login_required
def pharmacy_home(request):
    invoices_list = (
        Invoice.objects
        .select_related('patient', 'doctor')
        .annotate(
            paid_amount=Coalesce(
                Sum('payments__amount'),
                Value(0, output_field=DecimalField())
            ),
        )
        .annotate(
            balance_amount=Case(
                When(
                    paid_amount__lt=F('net_amount'),
                    then=ExpressionWrapper(
                        F('net_amount') - F('paid_amount'),
                        output_field=DecimalField(max_digits=10, decimal_places=2)
                    )
                ),
                default=Value(0),
                output_field=DecimalField(max_digits=10, decimal_places=2)
            ),
            refund_amount=Case(
                When(
                    paid_amount__gt=F('net_amount'),
                    then=ExpressionWrapper(
                        F('paid_amount') - F('net_amount'),
                        output_field=DecimalField(max_digits=10, decimal_places=2)
                    )
                ),
                default=Value(0),
                output_field=DecimalField(max_digits=10, decimal_places=2)
            ),
        )
        .order_by('-created_at')
    )
    
    # Pagination
    items_per_page = request.GET.get('per_page', 20)
    paginator = Paginator(invoices_list, items_per_page)
    
    page = request.GET.get('page', 1)
    try:
        invoices = paginator.page(page)
    except PageNotAnInteger:
        invoices = paginator.page(1)
    except EmptyPage:
        invoices = paginator.page(paginator.num_pages)

    context = {
        'invoices': invoices,
        'total_records': paginator.count,
    }

    return render(request, 'pharmacy/pharmacy.html', context)


@login_required
def generatebill(request):
    if request.method == 'POST':
        try:
            # Get form data
            patient_id = request.POST.get('patient_id')
            hospital_doctor_id = request.POST.get('hospital_doctor')
            prescription_no = request.POST.get('prescription')
            note = request.POST.get('note', '')
            
            # Totals
            total_amount = Decimal(request.POST.get('total_amount', 0))
            discount_amount = Decimal(request.POST.get('discount_amount', 0))
            tax_amount = Decimal(request.POST.get('tax_amount', 0))
            net_amount = Decimal(request.POST.get('net_amount', 0))
            
            # Payment
            payment_mode = request.POST.get('payment_mode')
            payment_amount = Decimal(request.POST.get('payment_amount', 0))
            
            # Validate required fields
            if not patient_id or not hospital_doctor_id:
                messages.error(request, 'Patient and Doctor are required!')
                return redirect('generatebill')
            
            # Get patient and doctor
            patient = Patient.objects.get(id=patient_id)
            doctor = Doctor.objects.get(id=hospital_doctor_id)
            
            # Use transaction to ensure data consistency
            with transaction.atomic():
                # Generate unique invoice number
                invoice_number = f"INV-{datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}"
                
                # Create Invoice
                invoice = Invoice.objects.create(
                    patient=patient,
                    doctor=doctor,
                    invoice_number=invoice_number,
                    total_amount=net_amount,
                    discount_amount=discount_amount,
                    status='PAID' if payment_amount >= net_amount else 'PENDING'
                )
                
                # Get medicine data
                medicines_data = request.POST.get('medicines_data')
                if medicines_data:
                    medicines = json.loads(medicines_data)
                    
                    for med in medicines:
                        drug = Drug.objects.get(id=med['drug_id'])
                        quantity = int(med['quantity'])
                        
                        # Check stock availability
                        if drug.stock_quantity < quantity:
                            raise ValueError(f"Insufficient stock for {drug.name}")
                        
                        # Create invoice item
                        InvoiceItem.objects.create(
                            invoice=invoice,
                            drug=drug,
                            quantity=quantity,
                            unit_price=Decimal(med['unit_price'])
                        )
                        
                        # Reduce stock
                        drug.stock_quantity -= quantity
                        drug.save()
                
                # Create payment if payment mode selected
                if payment_mode and payment_amount > 0:
                    Payment.objects.create(
                        invoice=invoice,
                        method=payment_mode,
                        amount=payment_amount,
                        reference=prescription_no or ''
                    )
                
                messages.success(request, f'Bill {invoice_number} created successfully!')
                return JsonResponse({
                    'success': True,
                    'invoice_number': invoice_number,
                    'message': 'Bill saved successfully!'
                })
        
        except Patient.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Patient not found'}, status=400)
        except Doctor.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Doctor not found'}, status=400)
        except Drug.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Medicine not found'}, status=400)
        except ValueError as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=400)
        except Exception as e:
            return JsonResponse({'success': False, 'error': f'Error: {str(e)}'}, status=500)
    
    # GET request - show form
    categories = DrugCategory.objects.all()
    doctors = Doctor.objects.filter(status__in=['Employed', 'Full-Time']).order_by('last_name', 'first_name')
    
    context = {
        'categories': categories,
        'doctors': doctors
    }
    
    return render(request, 'pharmacy/generatebill.html', context)


def get_medicines_by_category(request):
    category_id = request.GET.get('category_id')
    
    if category_id:
        try:
            medicines = Drug.objects.filter(
                category_id=category_id,
                is_active=True
            ).values('name').distinct().order_by('name')
            
            medicine_list = [{'id': med['name'], 'name': med['name']} for med in medicines]
            return JsonResponse({'medicines': medicine_list})
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)
    
    return JsonResponse({'medicines': []})


def get_batches_by_medicine(request):
    medicine_name = request.GET.get('medicine_name')
    
    if medicine_name:
        try:
            batches = Drug.objects.filter(
                name=medicine_name,
                is_active=True,
                stock_quantity__gt=0
            ).values(
                'id',
                'batch_number',
                'expiry_date',
                'stock_quantity',
                'unit_price',
                'strength',
                'unit'
            ).order_by('expiry_date')
            
            return JsonResponse({'batches': list(batches)})
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)
    
    return JsonResponse({'batches': []})


def get_patients(request):
    """Fetch patients based on search query"""
    query = request.GET.get('q', '')
    
    if len(query) >= 2:
        patients = Patient.objects.filter(
            first_name__icontains=query
        ) | Patient.objects.filter(
            last_name__icontains=query
        ) | Patient.objects.filter(
            hospital_number__icontains=query
        )
        
        patients = patients[:10]
        
        patient_list = [{
            'id': str(patient.id),
            'name': patient.full_name,
            'hospital_number': patient.hospital_number,
            'phone': patient.phone or ''
        } for patient in patients]
        
        return JsonResponse(patient_list, safe=False)
    
    return JsonResponse([], safe=False)


def get_batches(request):
    drug_id = request.GET.get('drug_id')
    
    if drug_id:
        drugs = Drug.objects.filter(id=drug_id, is_active=True).values(
            'id', 'batch_number', 'expiry_date', 'stock_quantity', 'unit_price'
        )
        
        batches = list(drugs)
        return JsonResponse({'batches': batches})
    
    return JsonResponse({'batches': []})