from django.db import models
from customer.models import *
from pre_designed.models import *

class FavoriteDress(models.Model):
    user = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='favorite_dresses')
    dress = models.ForeignKey(PreDesigned, on_delete=models.CASCADE, related_name='favorited_by')
    added_on = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} favorited {self.dress.name}"