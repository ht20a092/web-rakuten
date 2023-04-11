from django.db import models

class FavoriteProduct(models.Model):
    product_id = models.CharField(max_length=255, unique=True)
    name = models.CharField(max_length=255)
    image_url = models.URLField()
    price = models.IntegerField()
    initial_price = models.IntegerField()

    def __str__(self):
        return self.name