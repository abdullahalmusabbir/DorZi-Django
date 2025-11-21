from django.db import models
from django.contrib.auth.models import User

class Tailor(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='tailor')
    business_name = models.CharField(max_length=255)
    business_location = models.TextField()
    tailor_about = models.TextField(blank=True, null=True)
    business_description = models.TextField(blank=True, null=True)

    EXPERTISE_CHOICES = [
        ('Beginner', 'Beginner'),
        ('Intermediate', 'Intermediate'),
        ('Expert', 'Expert'),
    ]

    phone = models.CharField(max_length=15, blank=True, null=True)
    expertise = models.CharField(max_length=20, choices=EXPERTISE_CHOICES, default='Beginner')
    category = models.CharField(
        max_length=50,
        choices=[
            # Punjabi
            ('Short_Punjabi', 'Short Punjabi'),
            ('Long_Punjabi', 'Long Punjabi'),
            ('Designer_Punjabi', 'Designer Punjabi'),
            ('Embroidered_Punjabi', 'Embroidered Punjabi'),
            ('Kurta_Punjabi', 'Kurta Punjabi'),
            ('Traditional_Punjabi', 'Traditional Punjabi'),

            # Shirt
            ('Formal_Shirt', 'Formal Shirt'),
            ('Casual_Shirt', 'Casual Shirt'),
            ('Half_Sleeve_Shirt', 'Half Sleeve Shirt'),
            ('Denim_Shirt', 'Denim Shirt'),
            ('T_Shirt', 'T-Shirt'),
            ('Sleeveless_Shirt', 'Sleeveless Shirt'),
            ('Printed_Shirt', 'Printed Shirt'),

            # Pant
            ('Kurta', 'Kurta'),
            ('Formal_Pant', 'Formal Pant'),
            ('Jeans', 'Jeans'),
            ('Cargo_Pant', 'Cargo Pant'),
            ('Chinos', 'Chinos'),
            ('Trouser', 'Trouser'),
            ('Shorts', 'Shorts'),
            ('Leggings', 'Leggings'),

            # Women’s Dress
            ('Salwar_Kameez', 'Salwar Kameez'),
            ('Lehenga', 'Lehenga'),
            ('Blouse', 'Blouse'),
            ('Saree_Fall_Pleat', 'Saree Fall & Pleat'),
            ('Gown', 'Gown'),
            ('Maxi_Dress', 'Maxi Dress'),
            ('Anarkali', 'Anarkali'),
            ('Skirt', 'Skirt'),
            ('Palazzo', 'Palazzo'),
            ('Tops', 'Tops'),
            ('Kameez', 'Kameez'),
            ('Saree_Blouse', 'Saree Blouse'),
            ('Waistcoat', 'Waistcoat'),
            ('Jacket', 'Jacket'),
            ('Coat', 'Coat'),
            ('Sherwani', 'Sherwani'),
            ('Kids_Dress', 'Kids Dress'),

        ],
        blank=True,
        null=True,
        default='Formal_Shirt'
    )

    services_offered = models.TextField(
        blank=True,
        null=True,
        default="None"
    )

    DISTRICT_CHOICES = [
        ('dhaka', 'Dhaka'),
        ('chittagong', 'Chittagong'),
        ('khulna', 'Khulna'),
        ('rajshahi', 'Rajshahi'),
        ('sylhet', 'Sylhet'),
        ('barisal', 'Barisal'),
        ('rangpur', 'Rangpur'),
        ('mymensingh', 'Mymensingh'),
        ('comilla', 'Comilla'),
        ('gazipur', 'Gazipur'),
    ]
    
    district = models.CharField(max_length=100,choices=DISTRICT_CHOICES,blank=True,null=True)
    estimated_delivery_date = models.DateField(blank=True, null=True)  
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)
    NID = models.CharField(max_length=20, unique=True)
    purchased_products = models.JSONField(default=list)
    

    profile_picture = models.ImageField(upload_to="tailor_profiles/", blank=True, null=True)
    average_rating = models.FloatField(default=0.0)
    is_available = models.BooleanField(default=True)
    
    Chest = models.CharField(max_length=10, blank=True, null=True)
    waist = models.CharField(max_length=10, blank=True, null=True)
    hip = models.CharField(max_length=10, blank=True, null=True)
    shoulder = models.CharField(max_length=10, blank=True, null=True)
    sleeve = models.CharField(max_length=10, blank=True, null=True)
    neck = models.CharField(max_length=10, blank=True, null=True)
    length = models.CharField(max_length=10, blank=True, null=True)
    inseam = models.CharField(max_length=10, blank=True, null=True)
    
    
    total_earning = models.DecimalField(max_digits=12, decimal_places=2, default=0.0)


    def __str__(self):
        return f"{self.business_name} ({self.user.username})"