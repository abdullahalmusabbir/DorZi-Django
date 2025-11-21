from django.db import models
from tailor.models import Tailor
from pre_designed.models import PreDesigned
from customer.models import Customer

class Reviews(models.Model):
    customer = models.ForeignKey(
        Customer, 
        on_delete=models.CASCADE, 
        related_name='reviews',
        null=True,
        blank=True
    )

    tailor = models.ForeignKey(
        Tailor, 
        on_delete=models.CASCADE, 
        related_name='tailor_reviews',
        null=True,  
        blank=True 
    )  

    product = models.ForeignKey(
        PreDesigned, 
        on_delete=models.CASCADE, 
        related_name='dress_reviews',
        null=True, 
        blank=True
    )

    rating = models.IntegerField()  
    comment = models.TextField(blank=True, null=True)  
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('customer', 'product')  

    def save(self, *args, **kwargs):
        if self.rating < 1 or self.rating > 5:
            raise ValueError("Rating must be between 1 and 5.")
        
        # যদি product থাকে কিন্তু tailor না থাকে, তাহলে product এর tailor assign করুন
        if self.product and not self.tailor:
            self.tailor = self.product.tailor
            
        super().save(*args, **kwargs)

    def __str__(self):
        try:
            # Customer এর user থেকে username নিন
            customer_name = self.customer.user.username
        except AttributeError:
            customer_name = f"Customer-{self.customer.id}"
        
        if self.product:
            product_title = self.product.title if self.product else "Unknown Product"
            return f"Review by {customer_name} on {product_title} - {self.rating}/5"
        elif self.tailor:
            try:
                tailor_name = self.tailor.user.username
            except AttributeError:
                tailor_name = f"Tailor-{self.tailor.id}"
            return f"Review by {customer_name} on {tailor_name} - {self.rating}/5"
        else:
            return f"Review by {customer_name} - {self.rating}/5"
    
    def get_rating_display(self):
        return f"{self.rating} out of 5 stars"