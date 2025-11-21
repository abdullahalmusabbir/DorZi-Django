from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver


class Customer(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='customer', null=True, blank=True)
    
    chest = models.CharField(max_length=10, blank=True, null=True)
    waist = models.CharField(max_length=10, blank=True, null=True)
    hip = models.CharField(max_length=10, blank=True, null=True)
    shoulder = models.CharField(max_length=10, blank=True, null=True)
    sleeve = models.CharField(max_length=10, blank=True, null=True)
    neck = models.CharField(max_length=10, blank=True, null=True)
    length = models.CharField(max_length=10, blank=True, null=True)
    inseam = models.CharField(max_length=10, blank=True, null=True)

    phone = models.CharField(max_length=15, blank=True, null=True, default='01432941672')
    address = models.TextField(blank=True, null=True, default='Mirpur-12')
    profile_picture = models.ImageField(upload_to="customer_profiles/", blank=True, null=True)
    

    def __str__(self):
        return self.user.username if self.user else "No User"


# সিগন্যাল ফাংশন
@receiver(post_save, sender=User)
def create_customer_profile(sender, instance, created, **kwargs):
    """
    যখন নতুন User তৈরি হবে, তখন অটোমেটিক Customer প্রোফাইল তৈরি হবে
    """
    if created:
        Customer.objects.get_or_create(user=instance)

@receiver(post_save, sender=User)
def save_customer_profile(sender, instance, **kwargs):
    """
    User সেভ হলে Customer প্রোফাইল সেভ হবে
    """
    if hasattr(instance, 'customer'):
        instance.customer.save()