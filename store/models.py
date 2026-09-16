from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from decimal import Decimal, ROUND_HALF_UP


# Create your models here.


class Category(models.Model):
  
  name=models.CharField(max_length=100)
  image=models.ImageField(upload_to="categories/")
  created_at = models.DateTimeField(auto_now_add=True)

  def __str__(self):
    return self.name



class Product(models.Model):

    category = models.ForeignKey(Category,on_delete=models.CASCADE)
    name = models.CharField(max_length=200)
    brand = models.CharField(max_length=100)
    description = models.TextField()
    image = models.ImageField(upload_to="products/")
    price = models.DecimalField(max_digits=10, decimal_places=2)
    stock = models.PositiveIntegerField(default=0)
    available = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

    @property
    def active_offer(self):
        return next(
            (offer for offer in self.category.offers.all() if offer.is_active()),
            None,
        )

    def discounted_price(self, price):
        offer = self.active_offer
        if not offer:
            return price
        discount = Decimal("1") - (offer.discount_percent / Decimal("100"))
        return (price * discount).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    @property
    def display_price(self):
        return self.discounted_price(self.price)



class ProductVariant(models.Model):

    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name="variants"
    )

    size = models.CharField(
        max_length=50,
        blank=True,
        null=True
    )

    color = models.CharField(
        max_length=50,
        blank=True,
        null=True
    )

    other = models.CharField(
        max_length=100,
        blank=True,
        null=True
    )

    price = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )

    stock = models.PositiveIntegerField(
        default=0
    )

    available = models.BooleanField(
        default=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):

        options = []

        if self.size:
            options.append(self.size)

        if self.color:
            options.append(self.color)

        if self.other:
            options.append(self.other)

        variant_name = " / ".join(options)

        return f"{self.product.name} - {variant_name}"

    @property
    def active_offer(self):
        return self.product.active_offer

    @property
    def discounted_price(self):
        return self.product.discounted_price(self.price)



class Wishlist(models.Model):

    user = models.ForeignKey(User,on_delete=models.CASCADE)
    product = models.ForeignKey(Product,on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
      return f"{self.user.username} - {self.product.name}"


class Review(models.Model):

    RATING_CHOICES = (

        (1, "1 Star"),
        (2, "2 Stars"),
        (3, "3 Stars"),
        (4, "4 Stars"),
        (5, "5 Stars"),

    )

    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name="reviews"
        )

    user = models.ForeignKey(User,on_delete=models.CASCADE)
    rating = models.PositiveSmallIntegerField(choices=RATING_CHOICES)
    comment = models.TextField()
    created_at = models.DateTimeField(

        auto_now_add=True

    )

    class Meta:

        constraints = [
            models.UniqueConstraint(
               fields=["user", "product"],
                name="unique_review"
            )
        ]

    def __str__(self):
       return f"{self.user.username} - {self.product.name}"






class Coupon(models.Model):

    code = models.CharField(max_length=50,unique=True)
    discount_percent = models.DecimalField(max_digits=5,decimal_places=2)
    minimum_amount = models.DecimalField(max_digits=10,decimal_places=2,default=0)
    maximum_discount = models.DecimalField(max_digits=10,decimal_places=2,null=True,blank=True)
    valid_from = models.DateTimeField()
    valid_to = models.DateTimeField()
    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.code

    def is_valid(self):

        now = timezone.now()

        return (
            self.active
            and self.valid_from <= now
            and self.valid_to >= now
        )


class CategoryOffer(models.Model):

    category = models.ForeignKey(
        Category,
        on_delete=models.CASCADE,
        related_name="offers",
    )
    title = models.CharField(max_length=120)
    description = models.TextField()
    discount_percent = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
    )
    active = models.BooleanField(default=True)
    valid_from = models.DateTimeField(null=True, blank=True)
    valid_to = models.DateTimeField(null=True, blank=True)
    display_order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("display_order", "category__name", "-created_at")

    def __str__(self):
        return f"{self.category.name} - {self.title}"

    def is_active(self):
        now = timezone.now()
        return (
            self.active
            and (self.valid_from is None or self.valid_from <= now)
            and (self.valid_to is None or self.valid_to >= now)
        )


class ContactMessage(models.Model):

    STATUS_CHOICES = (
        ("new", "New"),
        ("in_progress", "In progress"),
        ("resolved", "Resolved"),
    )

    full_name = models.CharField(max_length=100)
    email = models.EmailField()
    subject = models.CharField(max_length=150)
    message = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="new")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-created_at",)

    def __str__(self):
        return f"{self.subject} - {self.full_name}"
    

