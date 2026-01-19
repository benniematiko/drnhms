from django.contrib import admin

# Register your models here.


from .models import DrugCategory,Drug, Supplier, DrugPurchase, DrugStockAdjustment, Pharmacy

admin.site.register(DrugCategory)
admin.site.register(Drug)
admin.site.register(Supplier)
admin.site.register(DrugPurchase)
admin.site.register(DrugStockAdjustment)
admin.site.register(Pharmacy)


