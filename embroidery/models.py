from django.db import models
from tailor.models import Tailor
from customer.models import Customer

# Create your models here.
class Embroidery(models.Model):
    tailor = models.ForeignKey(Tailor, on_delete=models.CASCADE, related_name="embroideries")

    title = models.CharField(max_length=100)  # ডিজাইনের নাম/শিরোনাম
    description = models.TextField(blank=True, null=True)  # ডিজাইনের বিস্তারিত
    design_image = models.ImageField(upload_to="embroidery_designs/", blank=True, null=True)  

    fabric_type = models.CharField(max_length=50, blank=True, null=True)  # যেমন: cotton, silk, linen
    thread_type = models.CharField(max_length=50, blank=True, null=True)  # যেমন: polyester, silk thread

    color = models.CharField(max_length=30, blank=True, null=True)  # প্রধান রঙ
    complexity_level = models.CharField(
        max_length=20,
        choices=[
            ("simple", "Simple"),
            ("medium", "Medium"),
            ("complex", "Complex"),
        ],
        default="simple"
    )

    price = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)
    estimated_time = models.DurationField(blank=True, null=True)  # কত সময় লাগবে
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


    def __str__(self):
        return f"{self.title} - {self.tailor.business_name}"
