from django.db import models
from customer.models import *
from tailor.models import Tailor

class FavoriteTailor(models.Model):
    user = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='favorite_tailors')
    tailor = models.ForeignKey(Tailor, on_delete=models.CASCADE, related_name='favorited_by')
    added_on = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} favorited {self.tailor.business_name}"