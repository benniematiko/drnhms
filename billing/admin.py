from django.contrib import admin

# Register your models here.


from .models import Invoice,InvoiceItem, Payment

admin.site.register(Invoice)
admin.site.register(InvoiceItem)
admin.site.register(Payment)

