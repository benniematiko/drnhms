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
from pharmacy.models import Supplier
from .models import DrugPurchase

# Save data into the database from purchasemedicine.html

from django.views.decorators.csrf import csrf_exempt
from datetime import datetime


# Display records on the medicinepurchaselist.html
# from django.db.models import F, ExpressionWrapper, DecimalField


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
        except Exception as e:            
            messages.error(request, f'Error creating bill: {str(e)}')
            return JsonResponse({'success': False, 'error': str(e)}, status=500)
        
        # except Patient.DoesNotExist:
        #     return JsonResponse({'success': False, 'error': 'Patient not found'}, status=400)
        # except Doctor.DoesNotExist:
        #     return JsonResponse({'success': False, 'error': 'Doctor not found'}, status=400)
        # except Drug.DoesNotExist:
        #     return JsonResponse({'success': False, 'error': 'Medicine not found'}, status=400)
        # except ValueError as e:
        #     return JsonResponse({'success': False, 'error': str(e)}, status=400)
        # except Exception as e:
        #     return JsonResponse({'success': False, 'error': f'Error: {str(e)}'}, status=500)
    
    # GET request - show form
    # ✅ NEW: Get patient info from URL parameters if available
    patient_id = request.GET.get('patient_id')
    patient_name = request.GET.get('patient_name', '')

    categories = DrugCategory.objects.all()
    doctors = Doctor.objects.filter(status__in=['Employed', 'Full-Time']).order_by('last_name', 'first_name')

    # categories = DrugCategory.objects.all()
    # doctors = Doctor.objects.filter(status__in=['Employed', 'Full-Time']).order_by('last_name', 'first_name')

    # ✅ NEW: If patient_id is provided, get the full patient object
    selected_patient = None
    if patient_id:
        try:
            selected_patient = Patient.objects.get(id=patient_id)
            patient_name = selected_patient.full_name
        except Patient.DoesNotExist:
            pass

    context = {
        'categories': categories,
        'doctors': doctors,
        'selected_patient': selected_patient,  # ✅ NEW
        'patient_name': patient_name,  # ✅ NEW
    }

    return render(request, 'pharmacy/generatebill.html', context)


    
    # context = {
    #     'categories': categories,
    #     'doctors': doctors
    # }
    
    # return render(request, 'pharmacy/generatebill.html', context)


@login_required
def get_medicines_by_category(request, category_id):
    """Fetch medicines based on category ID from URL"""
    try:
        medicines = Drug.objects.filter(
            category_id=category_id,
            is_active=True
        ).values('id', 'name').distinct().order_by('name')
        
        medicine_list = [{'id': med['id'], 'name': med['name']} for med in medicines]
        return JsonResponse({
            'status': 'success',
            'medicines': medicine_list
        })
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=400)

# view to handle medicine_id parameter:
@login_required
def get_batches_by_medicine(request):
    medicine_id = request.GET.get('medicine_id')  # Changed from medicine_name
    
    print(f"DEBUG: Searching batches for medicine_id: {medicine_id}")
    
    if medicine_id:
        try:
            batches = Drug.objects.filter(
                id=medicine_id,  # Changed to filter by ID
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
            
            batch_list = list(batches)
            print(f"DEBUG: Found {len(batch_list)} batches")
            
            if not batch_list:
                return JsonResponse({
                    'status': 'error',
                    'message': 'No batches available for this medicine',
                    'batches': []
                })
            
            return JsonResponse({
                'status': 'success',
                'batches': batch_list
            })
            
        except Exception as e:
            print(f"ERROR in get_batches_by_medicine: {str(e)}")
            return JsonResponse({
                'status': 'error',
                'message': str(e),
                'batches': []
            })
    
    return JsonResponse({
        'status': 'error',
        'message': 'Medicine ID is required',
        'batches': []
    })



@login_required
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

@login_required
def get_batches(request):
    drug_id = request.GET.get('drug_id')
    
    if drug_id:
        drugs = Drug.objects.filter(id=drug_id, is_active=True).values(
            'id', 'batch_number', 'expiry_date', 'stock_quantity', 'unit_price'
        )
        
        batches = list(drugs)
        return JsonResponse({'batches': batches})
    
    return JsonResponse({'batches': []})



@login_required
def medicinesearch(request):
    drugs = Drug.objects.select_related('category', 'pharmacy').filter(is_active=True)
    context = {
        'drugs': drugs
    }
    return render(request, 'pharmacy/medicinesearch.html', context)



# display drugs on the medicinesearch.html


@login_required
def drug_list(request):
    drugs = Drug.objects.select_related('category', 'pharmacy').filter(is_active=True)
    context = {
        'drugs': drugs
    }
    return render(request, 'pharmacy/drug_list.html', context)



# Getting suppliers and categories


@login_required
def purchasemedicine(request):
    suppliers = Supplier.objects.all()
    categories = DrugCategory.objects.all()    
    print(f"Total suppliers: {suppliers.count()}")  # Debug    
    for supplier in suppliers:
        print(f"Supplier: {supplier.name}, Active: {supplier.is_active}")    
    context = {
        'suppliers': suppliers,
        'categories': categories,
    }    
    return render(request, 'pharmacy/purchasemedicine.html', context)


# @login_required
# def medicinepurchaselist(request):
   
#     return render(request, 'pharmacy/medicinepurchaselist.html')


# display data on the medicinepurchaselist.html page

@login_required
def medicinepurchaselist(request):
    # Fetch all drug purchases with related data
    purchases_list = DrugPurchase.objects.select_related(
        'supplier', 
        'drug', 
        'drug__category'
    ).order_by('-purchase_date')
    
    # Add calculations for each purchase
    purchases_with_totals = []
    for purchase in purchases_list:
        total_amount = purchase.quantity * purchase.cost_price
        # You can add tax calculation here if needed
        tax_percentage = 0  # Modify as needed
        tax_amount = total_amount * Decimal(tax_percentage) / 100
        discount = Decimal('0.00')  # Modify as needed
        net_amount = total_amount + tax_amount - discount
        
        purchases_with_totals.append({
            'purchase': purchase,
            'total_amount': total_amount,
            'tax_percentage': tax_percentage,
            'tax_amount': tax_amount,
            'discount': discount,
            'net_amount': net_amount,
        })
    
    # Pagination
    items_per_page = request.GET.get('per_page', 20)
    paginator = Paginator(purchases_with_totals, items_per_page)
    
    page = request.GET.get('page', 1)
    try:
        purchases = paginator.page(page)
    except PageNotAnInteger:
        purchases = paginator.page(1)
    except EmptyPage:
        purchases = paginator.page(paginator.num_pages)
    
    context = {
        'purchases': purchases,
        'total_records': paginator.count,
    }
    
    return render(request, 'pharmacy/medicinepurchaselist.html', context)


# save date from purchasemedicine.html page

@login_required
def save_drug_purchase(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            
            # 1. Parse the date string you created (MM-DD-YYYY HH:MM AM/PM)
            date_str = data.get('purchase_date')
            clean_date = datetime.strptime(date_str, '%m-%d-%Y %I:%M %p').date()

            # 2. Get the objects
            drug = Drug.objects.get(id=data.get('drug_id'))
            supplier = Supplier.objects.get(id=data.get('supplier_id'))

            # 3. Create the DrugPurchase record
            # Your model's save() method will automatically increase the stock!
            purchase = DrugPurchase.objects.create(
                supplier=supplier,
                drug=drug,
                quantity=int(data.get('amount')), # Or however you define quantity
                cost_price=data.get('amount'), 
                purchase_date=clean_date,
                invoice_number=data.get('bill_no')
            )

            return JsonResponse({'status': 'success', 'purchase_id': purchase.id})
        
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)})

    return JsonResponse({'status': 'error', 'message': 'Invalid request'})



# SAVE DATA INTO DATABASE IN THE purchasemedicine.html page

def purchase_medicine_form(request):
    """Display the purchase medicine form"""
    suppliers = Supplier.objects.filter(is_active=True)
    categories = DrugCategory.objects.all()
    
    context = {
        'suppliers': suppliers,
        'categories': categories,
    }
    return render(request, 'pharmacy/purchasemedicine.html', context)


@csrf_exempt
def save_medicine_purchase(request):
    """Save medicine purchase data"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            
            # Extract main form data
            supplier_id = data.get('supplier_id')
            bill_no = data.get('bill_no')
            purchase_date = data.get('purchase_date')
            medicines = data.get('medicines', [])
            note = data.get('note', '')
            
            # Validate required fields
            if not supplier_id or not medicines:
                return JsonResponse({
                    'status': 'error',
                    'message': 'Supplier and at least one medicine are required'
                }, status=400)
            
            # Get supplier
            try:
                supplier = Supplier.objects.get(id=supplier_id)
            except Supplier.DoesNotExist:
                return JsonResponse({
                    'status': 'error',
                    'message': 'Invalid supplier selected'
                }, status=400)
            
            # Use transaction to ensure all saves succeed or none do
            with transaction.atomic():
                purchase_records = []
                
                for medicine in medicines:
                    drug_id = medicine.get('drug_id')
                    quantity = int(medicine.get('quantity', 0))
                    purchase_price = Decimal(medicine.get('purchase_price', 0))
                    batch_no = medicine.get('batch_no', '')
                    expiry_date = medicine.get('expiry_date')
                    
                    # Get or create drug
                    try:
                        drug = Drug.objects.get(id=drug_id)
                        
                        # Update drug details
                        drug.batch_number = batch_no
                        drug.expiry_date = expiry_date
                        if medicine.get('sale_price'):
                            drug.unit_price = Decimal(medicine.get('sale_price'))
                        drug.save()
                        
                    except Drug.DoesNotExist:
                        return JsonResponse({
                            'status': 'error',
                            'message': f'Drug with id {drug_id} not found'
                        }, status=400)
                    
                    # Create purchase record
                    purchase = DrugPurchase.objects.create(
                        supplier=supplier,
                        drug=drug,
                        quantity=quantity,
                        cost_price=purchase_price,
                        invoice_number=bill_no
                    )
                    purchase_records.append(purchase)
                
                return JsonResponse({
                    'status': 'success',
                    'message': f'Successfully saved {len(purchase_records)} medicine purchase(s)',
                    'bill_no': bill_no
                })
                
        except json.JSONDecodeError:
            return JsonResponse({
                'status': 'error',
                'message': 'Invalid JSON data'
            }, status=400)
        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'message': str(e)
            }, status=500)
    
    return JsonResponse({
        'status': 'error',
        'message': 'Invalid request method'
    }, status=405)



# Save data from generateBill pop up modal view


@login_required

def add_patient_from_bill(request):
    """Handle patient creation from the generate bill modal"""
    if request.method == 'POST':
        try:
            # Get form data
            full_name = request.POST.get('patient_full_name', '').strip()
            
            # Split full name into first and last name
            name_parts = full_name.split(' ', 1)
            first_name = name_parts[0]
            last_name = name_parts[1] if len(name_parts) > 1 else ''
            
            # Get all other fields
            gender = request.POST.get('gender')
            date_of_birth = request.POST.get('date_of_birth')
            guardian_name = request.POST.get('guardian_full_name', '')
            phone = request.POST.get('phone_number', '')
            email = request.POST.get('email', '')
            address = request.POST.get('address', '')
            blood_group = request.POST.get('blood_group', '')
            marital_status = request.POST.get('marital_status', '')
            allergies = request.POST.get('allergies', '')
            insurance_provider = request.POST.get('insurance', '')
            insurance_id = request.POST.get('insurance_id', '')
            national_id = request.POST.get('national_id', '')
            remarks = request.POST.get('remarks', '')
            
            # Validate required fields
            if not all([first_name, gender, date_of_birth]):
                messages.error(request, 'Please fill in all required fields (Name, Gender, Date of Birth)')
                return redirect('generatebill')
            
            # Generate unique hospital number
            last_patient = Patient.objects.order_by('-created_at').first()
            if last_patient and last_patient.hospital_number:
                try:
                    # Extract number part (assuming format like "PAT-000001")
                    last_num = int(last_patient.hospital_number.split('-')[-1])
                    new_num = last_num + 1
                except:
                    new_num = 1
            else:
                new_num = 1
            
            hospital_number = f"PAT-{new_num:06d}"
            
            # Create the patient with all fields
            patient = Patient.objects.create(
                hospital_number=hospital_number,
                first_name=first_name,
                last_name=last_name,
                gender=gender,
                date_of_birth=date_of_birth,
                guardian_name=guardian_name,
                phone=phone,
                email=email,
                address=address,
                blood_group=blood_group,
                marital_status=marital_status,
                allergies=allergies,
                insurance_provider=insurance_provider,
                insurance_id=insurance_id,
                national_id=national_id,
                remarks=remarks,
                status='Pending'  # Default status
            )
            
            # Success message
            messages.success(request, f'Patient {patient.full_name} added successfully!')
            
            # Redirect back to generate bill with the new patient selected
            return redirect(f'/pharmacy/pharmacy/generatebill/?patient_id={patient.id}&patient_name={patient.full_name}')
            
        except Exception as e:
            messages.error(request, f'Error creating patient: {str(e)}')
            return redirect('generatebill')
    
    return redirect('generatebill')



@login_required
@login_required
def add_patient_ajax(request):
    """AJAX version - returns JSON response without page reload"""
    if request.method == 'POST':
        try:
            # Get form data
            full_name = request.POST.get('patient_full_name', '').strip()
            
            # Split full name
            name_parts = full_name.split(' ', 1)
            first_name = name_parts[0]
            last_name = name_parts[1] if len(name_parts) > 1 else ''
            
            # Get all other fields
            gender = request.POST.get('gender')
            date_of_birth = request.POST.get('date_of_birth')
            guardian_name = request.POST.get('guardian_full_name', '')
            phone = request.POST.get('phone_number', '')
            email = request.POST.get('email', '')
            address = request.POST.get('address', '')
            blood_group = request.POST.get('blood_group', '')
            marital_status = request.POST.get('marital_status', '')
            allergies = request.POST.get('allergies', '')
            insurance_provider = request.POST.get('insurance', '')
            insurance_id = request.POST.get('insurance_id', '')
            national_id = request.POST.get('national_id', '')
            remarks = request.POST.get('remarks', '')
            
            # Validate required fields
            if not all([first_name, gender, date_of_birth]):
                return JsonResponse({
                    'success': False,
                    'message': 'Please fill in all required fields (Name, Gender, Date of Birth)'
                }, status=400)
            
            # Generate unique hospital number
            last_patient = Patient.objects.order_by('-created_at').first()
            if last_patient and last_patient.hospital_number:
                try:
                    last_num = int(last_patient.hospital_number.split('-')[-1])
                    new_num = last_num + 1
                except:
                    new_num = 1
            else:
                new_num = 1
            
            hospital_number = f"PAT-{new_num:06d}"
            
            # Create the patient
            patient = Patient.objects.create(
                hospital_number=hospital_number,
                first_name=first_name,
                last_name=last_name,
                gender=gender,
                date_of_birth=date_of_birth,
                guardian_name=guardian_name,
                phone=phone,
                email=email,
                address=address,
                blood_group=blood_group,
                marital_status=marital_status,
                allergies=allergies,
                insurance_provider=insurance_provider,
                insurance_id=insurance_id,
                national_id=national_id,
                remarks=remarks,
                status='Pending'
            )
            
            # Return success response with patient data
            return JsonResponse({
                'success': True,
                'message': f'Patient {patient.full_name} added successfully!',
                'patient': {
                    'id': str(patient.id),
                    'full_name': patient.full_name,
                    'hospital_number': patient.hospital_number
                }
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'Error creating patient: {str(e)}'
            }, status=500)
    
    return JsonResponse({
        'success': False,
        'message': 'Invalid request method'
    }, status=405)
