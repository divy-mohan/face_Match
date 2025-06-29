from django.db import models
from django.contrib.auth.models import User

class CompanyProfile(models.Model):
    name = models.CharField(max_length=200)
    logo = models.ImageField(upload_to='company/')
    about = models.TextField(blank=True)

    def __str__(self):
        return self.name

class JobCategory(models.Model):
    name = models.CharField(max_length=100)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)  # Superuser

    def __str__(self):
        return self.name

class JobTitle(models.Model):
    name = models.CharField(max_length=100)
    category = models.ForeignKey(JobCategory, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.name} ({self.category.name})"

class Supervisor(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    full_name = models.CharField(max_length=100)

    def __str__(self):
        return self.full_name

class Employee(models.Model):
    employee_number = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=100)
    face_image = models.ImageField(upload_to='employee_faces/', null=True, blank=True)  # Add this line
    job_title = models.ForeignKey(JobTitle, on_delete=models.SET_NULL, null=True)
    address = models.TextField()
    contact_number = models.CharField(max_length=20)
    email = models.EmailField(blank=True, null=True)
    supervisor = models.ForeignKey(Supervisor, on_delete=models.SET_NULL, null=True)
    face_encoding = models.BinaryField()  # Only encoding, no image

    def __str__(self):
        return f"{self.employee_number} - {self.name}"

class Attendance(models.Model):
    STATUS_CHOICES = (
        ('coming', 'Coming'),
        ('going', 'Going'),
    )
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE)
    image = models.ImageField(upload_to='attendance_images/', null=True, blank=True)  # Add this line
    date = models.DateField(auto_now_add=True)
    time = models.TimeField(auto_now_add=True)
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    marked_by = models.ForeignKey(Supervisor, on_delete=models.SET_NULL, null=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='coming')  # <-- Add this line

    class Meta:
        unique_together = ('employee', 'date', 'status')  # Allow both coming and going per day
        indexes = [
            models.Index(fields=['date']),
            models.Index(fields=['employee']),
        ]

    def __str__(self):
        return f"{self.employee} - {self.date} {self.time}"
    
    