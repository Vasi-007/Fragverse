from django.db import models
from django.contrib.auth.models import User
from store.models import Product
import uuid

# Create your models here.
class Order(models.Model):

    STATUS = (
        ("Pending", "Pending"),
        ("Processing", "Processing"),
        ("Shipped", "Shipped"),
        ("Delivered", "Delivered"),
        ("Cancelled", "Cancelled"),
    )

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    order_number= models.CharField(max_length=20,unique=True,editable=False,null=True,blank=True)

    phone = models.CharField(max_length=20)
    address = models.TextField()
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    country = models.CharField(max_length=100)
    postal_code = models.CharField(max_length=20)

    total = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )

    razorpay_order_id = models.CharField(
        max_length=100,
        blank=True,
        null=True
    )

    razorpay_payment_id = models.CharField(
        max_length=100,
        blank=True,
        null=True
    )

    created = models.DateTimeField(auto_now_add=True)

    status = models.CharField(
        max_length=20,
        choices=STATUS,
        default="Pending"
    )
    def save(self, *args, **kwargs):

        if not self.order_number:
            self.order_number = (
                "FV-" + uuid.uuid4().hex[:8].upper()
            )

        super().save(*args, **kwargs)


    def __str__(self):
        return self.order_number

    


class OrderItem(models.Model):

    order = models.ForeignKey(Order,related_name="items",on_delete=models.CASCADE)
    product = models.ForeignKey(Product,on_delete=models.CASCADE)
    price = models.DecimalField(max_digits=10,decimal_places=2)
    quantity = models.PositiveIntegerField(default=1)

    def __str__(self):
        return self.product.name