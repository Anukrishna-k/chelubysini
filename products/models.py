from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator

class Category(models.Model):
    name = models.CharField(max_length=100)
    image = models.ImageField(upload_to='categories/', blank=True, null=True)

    class Meta:
        verbose_name_plural = "Categories"

    def __str__(self):
        return self.name

class Product(models.Model):
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='products')
    name = models.CharField(max_length=200)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    image = models.ImageField(upload_to='products/')
    stock = models.IntegerField(default=0)
    featured = models.BooleanField(default=False)
    best_seller = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

    @property
    def average_rating(self):
        reviews = self.reviews.all()
        if reviews.exists():
            return round(sum(r.rating for r in reviews) / reviews.count(), 1)
        return 0.0

class Review(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='reviews')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    rating = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    comment = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username}'s review of {self.product.name} ({self.rating}/5)"

class Coupon(models.Model):
    code = models.CharField(max_length=50, unique=True)
    discount_percent = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(100)])
    active = models.BooleanField(default=True)
    valid_until = models.DateTimeField()

    def __str__(self):
        return f"{self.code} ({self.discount_percent}% off)"

class HappyCustomer(models.Model):
    name = models.CharField(max_length=100)
    image = models.ImageField(upload_to='happy_customers/')
    quote = models.TextField(blank=True, null=True)
    location = models.CharField(max_length=100, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Happy Customer: {self.name}"


class HeroSlide(models.Model):
    subtitle = models.CharField(max_length=100, default="Fan favourites", help_text="Small text above main heading")
    title = models.CharField(max_length=200, default="Customer-loved Chelu classic", help_text="Main heading of the slide")
    image = models.ImageField(upload_to='hero_slides/', help_text="Saree photo or showcase image")
    button_text = models.CharField(max_length=50, default="SHOP NOW", help_text="Call to action button text")
    button_url = models.CharField(max_length=200, default="/shop/", help_text="URL / shop category URL to redirect to")
    order = models.PositiveIntegerField(default=0, help_text="Display order (lower is first)")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['order', '-created_at']

    def __str__(self):
        return f"{self.subtitle} - {self.title}"


class BoutiqueSettings(models.Model):
    store_name = models.CharField(max_length=200, default="Chelu by Sini")
    address = models.TextField(default="Sini's Design Studio, Bangalore, India")
    phone = models.CharField(max_length=50, default="+91 94973 60705")
    email = models.EmailField(default="support@chelubysini.com")
    shipping_rate = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    hours = models.CharField(max_length=200, default="Mon - Sat: 10:00 AM - 7:00 PM")
    upi_qr_code = models.ImageField(upload_to='settings/', blank=True, null=True)

    def __str__(self):
        return self.store_name





