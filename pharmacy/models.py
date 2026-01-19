from django.db import models

# Create your models here.

class Pharmacy(models.Model):
    
    name = models.CharField(max_length=255)
    address = models.TextField()
    phone_number = models.CharField(max_length=20)
    email = models.EmailField(blank=True, null=True)
    opening_hours = models.CharField(max_length=100)
    
    class Meta:
        verbose_name = "Pharmacy"         # singular name
        verbose_name_plural = "Pharmacy"  # plural name (no automatic 's' added)

    def __str__(self):
        return self.name
    
class DrugCategory(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)

    class Meta:
        verbose_name_plural = "Drug Categories"
        ordering = ['name']

    def __str__(self):
        return self.name


class Drug(models.Model):
    UNIT_CHOICES = (
        ('Tablet', 'Tablet'),
        ('Capsule', 'Capsule'),
        ('Syrup', 'Syrup'),
        ('Injection', 'Injection'),
        ('Cream', 'Cream'),
    )

    name = models.CharField(max_length=150)
    category = models.ForeignKey(
        DrugCategory, on_delete=models.SET_NULL, null=True, related_name='drugs'
    )
    unit = models.CharField(max_length=50, choices=UNIT_CHOICES)
    strength = models.CharField(max_length=50, blank=True)  # e.g., 500mg
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    stock_quantity = models.PositiveIntegerField(default=0)
    expiry_date = models.DateField()
    batch_number = models.CharField(max_length=50)
    manufacturer = models.CharField(max_length=150, blank=True)
    pharmacy = models.ForeignKey(Pharmacy, on_delete=models.CASCADE,related_name='drugs',null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['name']
        indexes = [
            models.Index(fields=['name']),
            models.Index(fields=['expiry_date']),
        ]

    def __str__(self):
        return f"{self.name} ({self.strength})"
    

class Supplier(models.Model):
    name = models.CharField(max_length=150)
    phone = models.CharField(max_length=20)
    email = models.EmailField(blank=True)
    address = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name


class DrugPurchase(models.Model):
    supplier = models.ForeignKey(Supplier, on_delete=models.PROTECT, related_name='purchases')
    drug = models.ForeignKey(Drug, on_delete=models.PROTECT, related_name='purchases')
    quantity = models.PositiveIntegerField()
    cost_price = models.DecimalField(max_digits=10, decimal_places=2)
    purchase_date = models.DateField(auto_now_add=True)
    invoice_number = models.CharField(max_length=50)

    def save(self, *args, **kwargs):
        # Increase stock automatically
        self.drug.stock_quantity += self.quantity
        self.drug.save(update_fields=['stock_quantity'])
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.drug.name} - {self.quantity}"


class DrugStockAdjustment(models.Model):
    ADJUSTMENT_REASON = (
        ('EXPIRED', 'Expired'),
        ('DAMAGED', 'Damaged'),
        ('LOSS', 'Loss'),
        ('CORRECTION', 'Correction'),
    )

    drug = models.ForeignKey(Drug, on_delete=models.CASCADE)
    quantity_change = models.IntegerField()
    reason = models.CharField(max_length=20, choices=ADJUSTMENT_REASON)
    note = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        self.drug.stock_quantity += self.quantity_change
        self.drug.save(update_fields=['stock_quantity'])
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.drug.name} ({self.quantity_change})"
    

