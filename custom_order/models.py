from django.db import models
from django.contrib.auth.models import User  
from django.utils.timezone import now
from tailor.models import *
from customer.models import *
from embroidery.models import *
from fabrics.models import *
from django.contrib.auth.models import User

class TOrders(models.Model):
    category = models.CharField(
        max_length=50,
        choices=[
            # Punjabi
            ('short_punjabi', 'Short Punjabi'),
            ('long_punjabi', 'Long Punjabi'),
            ('designer_punjabi', 'Designer Punjabi'),
            ('embroidered_punjabi', 'Embroidered Punjabi'),
            ('kurta_punjabi', 'Kurta Punjabi'),
            ('traditional_punjabi', 'Traditional Punjabi'),

            # Shirt
            ('formal_shirt', 'Formal Shirt'),
            ('casual_shirt', 'Casual Shirt'),
            ('half_sleeve_shirt', 'Half Sleeve Shirt'),
            ('denim_shirt', 'Denim Shirt'),
            ('tshirt', 'T-Shirt'),
            ('sleeveless_shirt', 'Sleeveless Shirt'),
            ('printed_shirt', 'Printed Shirt'),

            # Pant
            ('kurta', 'Kurta'),
            ('formal_pant', 'Formal Pant'),
            ('jeans', 'Jeans'),
            ('cargo_pant', 'Cargo Pant'),
            ('chinos', 'Chinos'),
            ('trouser', 'Trouser'),
            ('shorts', 'Shorts'),
            ('leggings', 'Leggings'),

            # Women’s Dress
            ('salwar_kameez', 'Salwar Kameez'),
            ('lehenga', 'Lehenga'),
            ('blouse', 'Blouse'),
            ('saree_fall_pleat', 'Saree Fall & Pleat'),
            ('gown', 'Gown'),
            ('maxi_dress', 'Maxi Dress'),
            ('anarkali', 'Anarkali'),
            ('skirt', 'Skirt'),
            ('palazzo', 'Palazzo'),
            ('tops', 'Tops'),
            ('kameez', 'Kameez'),
            ('saree_blouse', 'Saree Blouse'),
            ('waistcoat', 'Waistcoat'),
            ('jacket', 'Jacket'),
            ('coat', 'Coat'),
            ('sherwani', 'Sherwani'),
            ('kids_dress', 'Kids Dress'),
            
        ],
        blank=True,
        null=True,
        default='None'
    )

    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='torders')
    tailor = models.ForeignKey(Tailor, on_delete=models.CASCADE, related_name='torders')
    embroidery = models.ForeignKey(Embroidery, on_delete=models.SET_NULL, related_name='torders', null=True, blank=True)
    fabrics = models.ForeignKey(Fabric, on_delete=models.SET_NULL, related_name='torders', null=True, blank=True)
    
    order_date = models.DateTimeField(auto_now_add=True)
    address = models.TextField()
    contact_number = models.CharField(max_length=11, blank=True, null=True)  
    gender = models.CharField(max_length=10, blank=True, null=True)
    
    occasion = models.CharField(max_length=50, blank=True, null=True)  
    garment_type = models.CharField(max_length=50,blank=True, null=True)  # Increased max_length for flexibility
    
    inspiration = models.TextField(blank=True, null=True)  # Allowing null or blank values
    detailed_description = models.TextField(blank=True, null=True)  # Allowing null or blank values
    special_requests = models.TextField(blank=True, null=True)  # Allowing null or blank values
    delivery_date = models.DateField(blank=True, null=True)  # Fixed default=None issue
    price = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)  # Price of the order

    chest = models.CharField(max_length=10, blank=True, null=True)
    waist = models.CharField(max_length=10, blank=True, null=True)
    hip = models.CharField(max_length=10, blank=True, null=True)
    shoulder = models.CharField(max_length=10, blank=True, null=True)
    sleeve = models.CharField(max_length=10, blank=True, null=True)
    neck = models.CharField(max_length=10, blank=True, null=True)
    length = models.CharField(max_length=10, blank=True, null=True)
    inseam = models.CharField(max_length=10, blank=True, null=True)
    
    meter = models.DecimalField(max_digits=10, decimal_places=2, default=0.0, help_text="Length in meters")
    
    measurements_confirmed = models.DateField(null=True, blank=True, default=None)
    fabric_selected = models.DateField(null=True, blank=True, default=None)
    cutting_started = models.DateField(null=True, blank=True, default=None)
    stitching_started = models.DateField(null=True, blank=True, default=None)
    deliver = models.DateField(null=True, blank=True, default=None)

    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('shipped', 'Shipped'),
        ('delivered', 'Delivered'),
        ('canceled', 'Canceled'),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')  # Order Status
    
    selected_embroidery_info = models.TextField(blank=True, null=True)  # Store multiple embroidery as JSON
    embroidery_total_price = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)
    fabric_total_price = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)
    
    def get_total_price(self):
        """
        Calculate total price: tailor's base price + embroidery price + fabric price
        """
        base_price = 0
        embroidery_price = 0
        fabric_price = 0
        
        # Get tailor's base price
        if self.tailor and hasattr(self.tailor, 'price'):
            base_price = self.tailor.price or 0
        
        # Get embroidery price if exists
        if self.embroidery and hasattr(self.embroidery, 'price'):
            embroidery_price = self.embroidery.price or 0
        
        # Get fabric total price if exists
        if self.fabrics and hasattr(self.fabrics, 'total_price'):
            fabric_price = self.fabrics.total_price or 0
        
        total_price = base_price + embroidery_price + fabric_price
        
        # If a manual price is set, use that instead
        if self.price:
            return self.price
        
        return total_price
    
    def save(self, *args, **kwargs):
        """
        Automatically calculate and set the price when saving
        """
        if not self.price:
            self.price = self.get_total_price()
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.contact_number} - {self.tailor.business_name}"
