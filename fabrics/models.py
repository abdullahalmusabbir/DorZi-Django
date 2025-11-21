from django.db import models
from tailor.models import Tailor  # যদি fabric tailor upload করে

class Fabric(models.Model):
    tailor = models.ForeignKey(Tailor, on_delete=models.CASCADE, related_name="fabrics", blank=True, null=True)
    name = models.CharField(max_length=100)  # কাপড়ের নাম (যেমন: Cotton, Silk, Linen)
    description = models.TextField(blank=True, null=True)  # বিস্তারিত
    
    fabric_type = models.CharField(
        max_length=50,
        choices=[
            ("cotton", "Cotton"),
            ("silk", "Silk"),
            ("linen", "Linen"),
            ("wool", "Wool"),
            ("polyester", "Polyester"),
            ("blend", "Blend"),
            ("other", "Other"),
        ],
        default="cotton"
    )

    color = models.CharField(max_length=30, blank=True, null=True)  # যেমন: Red, Blue, Black
    pattern = models.CharField(
        max_length=50,
        choices=[
            ("plain", "Plain"),
            ("striped", "Striped"),
            ("checked", "Checked"),
            ("printed", "Printed"),
            ("embroidered", "Embroidered"),
        ],
        default="plain"
    )

    texture = models.CharField(max_length=50, blank=True, null=True)  # যেমন: Soft, Rough, Smooth
    width = models.DecimalField(max_digits=6, decimal_places=2, default=0.0, help_text="Fabric width in inches/cm")
    length_available = models.DecimalField(max_digits=10, decimal_places=2, default=0.0, help_text="Available fabric in meters")

    price_per_meter = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)
    image = models.ImageField(upload_to="fabric_images/", blank=True, null=True)

    is_available = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    

    def __str__(self):
        return f"{self.name} - {self.color} ({self.fabric_type})"
