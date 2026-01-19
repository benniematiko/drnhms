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


