from django.shortcuts import render

# Create your views here.



from django.contrib.auth.decorators import login_required
from .models import Invoice


# Save data into database starts here


from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
import json
from django.db import transaction
from datetime import datetime
from .models import Invoice, InvoiceItem, Payment
from patients.models import Patient
from doctors.models import Doctor
from pharmacy.models import Drug



@login_required
def billings_home(request):
    # Get all billings from the database
    billings = Invoice.objects.all()   
    return render(request, 'billings/billings.html', {'billings': billings})



# Save to the database starts here
@require_http_methods(["POST"])
def save_bill(request):
    """
    Handle saving of billing/invoice data
    """
    try:
        # Parse JSON data
        data = json.loads(request.body)
        
        # Extract data
        patient_id = data.get('patient_id')
        prescription_no = data.get('prescription_no')
        hospital_doctor_id = data.get('hospital_doctor')
        external_doctor_id = data.get('external_doctor')
        total_amount = data.get('total_amount', 0)
        discount_amount = data.get('discount_amount', 0)
        net_amount = data.get('net_amount', 0)
        payment_mode = data.get('payment_mode')
        payment_amount = data.get('payment_amount', 0)
        invoice_items = data.get('invoice_items', [])
        
        # Validate required fields
        if not patient_id:
            return JsonResponse({'success': False, 'error': 'Patient ID is required'})
        
        # Get patient
        try:
            patient = Patient.objects.get(id=patient_id)  # Changed variable name from patient_id to patient
        except Patient.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Patient not found'})
        
        # Get doctor
        doctor_id = hospital_doctor_id or external_doctor_id
        if not doctor_id:
            return JsonResponse({'success': False, 'error': 'Doctor is required'})
        
        try:
            doctor = Doctor.objects.get(id=doctor_id)
        except Doctor.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Doctor not found'})
        
        # Use atomic transaction to ensure data consistency
        with transaction.atomic():
            # Generate invoice number
            last_invoice = Invoice.objects.order_by('-created_at').first()
            if last_invoice and last_invoice.invoice_number:
                # Extract number from last invoice (e.g., "INV-0001" -> 1)
                try:
                    last_num = int(last_invoice.invoice_number.split('-')[-1])
                    new_num = last_num + 1
                except:
                    new_num = 1
            else:
                new_num = 1
            
            invoice_number = f"INV-{new_num:04d}"
            
            # Create Invoice
            invoice = Invoice.objects.create(
                patient=patient,
                doctor=doctor,
                invoice_number=invoice_number,
                total_amount=total_amount,
                discount_amount=discount_amount,
                net_amount=net_amount,  # Added net_amount field
                status='PENDING'
            )
            
            # Create Invoice Items
            for item_data in invoice_items:
                drug_id = item_data.get('drug_id')
                quantity = item_data.get('quantity')
                unit_price = item_data.get('unit_price')
                
                if not all([drug_id, quantity, unit_price]):
                    continue
                
                try:
                    drug = Drug.objects.get(id=drug_id)
                    
                    # Check stock availability
                    if drug.stock_quantity < quantity:
                        raise ValueError(f"Insufficient stock for {drug.name}")
                    
                    # Create invoice item
                    InvoiceItem.objects.create(
                        invoice=invoice,
                        drug=drug,
                        quantity=quantity,
                        unit_price=unit_price
                    )
                    
                    # Reduce stock
                    drug.stock_quantity -= quantity
                    drug.save(update_fields=['stock_quantity'])
                    
                except Drug.DoesNotExist:
                    continue
                except ValueError as e:
                    transaction.set_rollback(True)
                    return JsonResponse({'success': False, 'error': str(e)})
            
            # Create Payment if payment mode and amount provided
            if payment_mode and payment_amount > 0:
                Payment.objects.create(
                    invoice=invoice,
                    method=payment_mode,
                    amount=payment_amount
                )
                
                # Update invoice status if fully paid
                if payment_amount >= net_amount:
                    invoice.status = 'PAID'
                    invoice.save(update_fields=['status'])
        
        return JsonResponse({
            'success': True,
            'invoice_number': invoice_number,
            'invoice_id': str(invoice.id)
        })
        
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Invalid JSON data'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})