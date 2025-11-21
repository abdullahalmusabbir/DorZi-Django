from django.db import models
from tailor.models import Tailor

class PreDesigned(models.Model):
    tailor = models.ForeignKey(Tailor, on_delete=models.CASCADE, related_name='pre_designed')
    title = models.CharField(max_length=100)  
    description = models.TextField(blank=True, null=True)  
    availability = models.PositiveIntegerField(default=0)  
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)
    Categories = [
        ('Saree', 'Saree'),
        ('Salwar Kameez', 'Salwar Kameez'),
        ('Punjabi', 'Punjabi'),
        ('Formal Wear', 'Formal Wear'),
        ('Casual Wear', 'Casual Wear'),
        ('Western Wear', 'Western Wear'),
        ('Suits & Blazers', 'Suits & Blazers'),
    ]
    category = models.CharField(max_length=100,choices= Categories, blank=True, null=True)
    
    fabric_type = models.CharField(max_length=50, blank=True, null=True)  
    thread_type = models.CharField(max_length=50, blank=True, null=True)  
    color = models.CharField(max_length=30, blank=True, null=True)  
    estimated_time = models.DurationField(blank=True, null=True)  

    GENDER_CHOICES = [
        ('male', 'Male'),
        ('female', 'Female'),
        ('other', 'Other'),
    ]
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES, blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.title} - {self.tailor.business_name}"


class Image(models.Model):
    predesigned = models.ForeignKey(PreDesigned, on_delete=models.CASCADE, related_name="images")
    image = models.ImageField(upload_to='photos/')

    def __str__(self):
        return f"Image for {self.predesigned.title}"
