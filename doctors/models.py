from django.db import models

from django.contrib.auth.models import User

# Gender choices
GENDER_CHOICES = (
    ('M', 'Male'),
    ('F', 'Female'),
    ('O', 'Other'),
)

# Specialty choices
SPECIALTY_CHOICES = (
    ('Gynaecology', 'Gynaecology'),
    ('Dentist', 'Dentist'),
    ('Surgeon', 'Surgeon'),
)

# Employment status choices
STATUS_CHOICES = (
    ('Employed', 'Employed'),
    ('Terminated', 'Terminated'),
    ('Resigned', 'Resigned'),
    ('Full-Time', 'Full-Time'),  # consider adding 'Part-Time' if needed
)

class Doctor(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES, default='M')
    phone_number = models.CharField(max_length=20, blank=True)
    email = models.EmailField(unique=True)
    specialty = models.CharField(max_length=50, choices=SPECIALTY_CHOICES, default='Gynaecology')

    # created_at = models.DateTimeField(auto_now_add=True)
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Full-Time')
    
    office_address = models.TextField(blank=True)
    bio = models.TextField(blank=True)

    class Meta:
        ordering = ['last_name', 'first_name']

    def __str__(self):
        return f"{self.first_name} {self.last_name}"
    

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"

