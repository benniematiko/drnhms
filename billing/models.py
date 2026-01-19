from django.db import models

# Create your models here.


import uuid
from patients.models import Patient
from doctors.models import Doctor
from pharmacy.models import Drug
from django.db.models import Sum







class Invoice(models.Model):
    PAYMENT_STATUS = (
        ('PENDING', 'Pending'),
        ('PAID', 'Paid'),
        ('CANCELLED', 'Cancelled'),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    patient = models.ForeignKey(Patient, on_delete=models.PROTECT)
    doctor = models.ForeignKey(Doctor, on_delete=models.PROTECT)    
    invoice_number = models.CharField(max_length=30, unique=True)
    status = models.CharField(max_length=10, choices=PAYMENT_STATUS, default='PENDING')
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    discount_amount = models.DecimalField(max_digits=12,decimal_places=2,default=0.00)
    net_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)  # ✅ Add this
    
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['invoice_number']),
            models.Index(fields=['status']),
        ]

    def __str__(self):
        return self.invoice_number
    

class InvoiceItem(models.Model):
    invoice = models.ForeignKey(
        Invoice, related_name='items', on_delete=models.CASCADE
    )
    drug = models.ForeignKey(Drug, on_delete=models.PROTECT)
    quantity = models.PositiveIntegerField()
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    line_total = models.DecimalField(
        max_digits=12, decimal_places=2, editable=False
    )

    def save(self, *args, **kwargs):
        self.line_total = self.quantity * self.unit_price
        super().save(*args, **kwargs)

        # Update invoice total
        total = self.invoice.items.aggregate(
            total=Sum('line_total')
        )['total'] or 0
        self.invoice.total_amount = total
        self.invoice.save(update_fields=['total_amount'])

    def __str__(self):
        return f"{self.drug.name} x {self.quantity}"



class Payment(models.Model):
    PAYMENT_METHODS = (
        ('CASH', 'Cash'),
        ('CARD', 'Card'),
        ('TRANSFER', 'Bank Transfer'),
    )

    invoice = models.ForeignKey(
        Invoice, related_name='payments', on_delete=models.CASCADE
    )
    method = models.CharField(max_length=10, choices=PAYMENT_METHODS)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    payment_date = models.DateTimeField(auto_now_add=True)
    reference = models.CharField(max_length=100, blank=True)

    def __str__(self):
        return f"{self.invoice.invoice_number} - {self.amount}"



# billing/models.py
class Refund(models.Model):
    invoice = models.ForeignKey(
        Invoice, related_name='refunds', on_delete=models.CASCADE
    )
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    reason = models.CharField(max_length=255, blank=True)
    refunded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.invoice.invoice_number} - Refund {self.amount}"
