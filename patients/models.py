from django.db import models

import uuid # added this 

# Create your models here.

class Patient(models.Model):
    GENDER_CHOICES = (
        ('M', 'Male'),
        ('F', 'Female'),
    )

    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Cancelled', 'Cancelled'),
        ('Completed', 'Completed'),
    ]


    ACTION_CHOICES = [
        ('Update', 'Update'),
        ('Delete', 'Delete'),
        ('Edit', 'Edit'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    hospital_number = models.CharField(max_length=20, unique=True)

    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES)
    date_of_birth = models.DateField()    
    phone = models.CharField(max_length=15, blank=True, null=True)
    email = models.EmailField(max_length=254, blank=True, null=True)
    address = models.TextField()
    doctor = models.ForeignKey('doctors.Doctor', on_delete=models.CASCADE, null=True, blank=True)
    last_visit = models.DateTimeField(auto_now=True)      # Updates every time the record is saved
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending')

    # additional fields added in order to save data from popup modal

    blood_group = models.CharField(max_length=10, blank=True)
    marital_status = models.CharField(max_length=20, blank=True)
    guardian_name = models.CharField(max_length=200, blank=True)
    allergies = models.TextField(blank=True)
    insurance_provider = models.CharField(max_length=100, blank=True)
    insurance_id = models.CharField(max_length=100, blank=True)
    national_id = models.CharField(max_length=50, blank=True)
    remarks = models.TextField(blank=True)

    actiontaken = models.CharField(
        max_length=10,   # Long enough for the longest choice
        choices=ACTION_CHOICES,
        blank=True,      # Optional
        null=True        # Optional
    )

    created_at = models.DateTimeField(auto_now_add=True)  # Only set once on creation
   

    def __str__(self):
        return f"{self.hospital_number} - {self.first_name} {self.last_name}"
    
    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"


