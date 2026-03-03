from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
from django.utils import timezone


class UserManager(BaseUserManager):
    def create_user(self, email, full_name, role, password=None, **extra_fields):
        if not email:
            raise ValueError('The Email field must be set')
        email = self.normalize_email(email)
        user = self.model(email=email, full_name=full_name, role=role, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, full_name, role, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(email, full_name, role, password, **extra_fields)


class User(AbstractUser):
    ROLE_CHOICES = [
        ('Admin', 'Admin'),
        ('Farmer', 'Farmer'),
        ('Buyer', 'Buyer'),
    ]

    # Set username to null/blank since we use email
    username = models.CharField(max_length=150, unique=True, blank=True, null=True)
    email = models.EmailField(unique=True)
    full_name = models.CharField(max_length=100)
    role = models.CharField(max_length=10, choices=ROLE_CHOICES)
    address = models.TextField(null=True, blank=True)
    phone_number = models.CharField(max_length=15, null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now)

    objects = UserManager()  # Connect the new manager

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['full_name', 'role']

    def __str__(self):
        return f"{self.email} ({self.role})"


class AIConsultation(models.Model):
    farmer = models.ForeignKey(User, on_delete=models.CASCADE)
    image = models.ImageField(upload_to='crop_diseases/')
    prediction_type = models.CharField(max_length=20) # 'CNN' or 'Gemini'
    disease_name = models.CharField(max_length=200)
    recommendation = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

class NewsUpdate(models.Model):
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    content = models.TextField()
    category = models.CharField(max_length=50, choices=[
        ('General', 'General'),
        ('Market Price', 'Market Price'),
        ('Weather Alert', 'Weather Alert'),
        ('Advice', 'Expert Advice')
    ])
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

class Product(models.Model):
    CATEGORY_CHOICES = [
        ('Grain', 'Grains/Cereals'),
        ('Vegetable', 'Vegetables'),
        ('Fruit', 'Fruits'),
        ('Spices', 'Spices'),
    ]

    farmer = models.ForeignKey(User, on_delete=models.CASCADE)
    crop_name = models.CharField(max_length=100)
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES, default='Grain')
    description = models.TextField()
    price_per_unit = models.DecimalField(max_digits=10, decimal_places=2)
    quantity_available = models.PositiveIntegerField() # Matching the form
    image = models.ImageField(upload_to='market_products/') # Matching the form
    is_available = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.crop_name



class Review(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='reviews')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    rating = models.IntegerField(default=5) # e.g., 1 to 5 stars
    comment = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Review by {self.user.username} for {self.product.crop_name}"

class Notification(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE) # The person receiving the notification (Farmer)
    message = models.CharField(max_length=255)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Notification for {self.user.username}"

    class Equipment(models.Model):
        owner = models.ForeignKey(User, on_delete=models.CASCADE)
        equipment_name = models.CharField(max_length=100)
        description = models.TextField()

        # Allow them to charge by hour, day, or both
        rate_per_hour = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
        rate_per_day = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)

        image = models.ImageField(upload_to='equipment/')
        is_available = models.BooleanField(default=True)
        created_at = models.DateTimeField(auto_now_add=True)

        def __str__(self):
            return f"{self.equipment_name} - {self.owner.username}"


class Equipment(models.Model):
    owner = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=100, help_text="e.g., Tractor, Harvester, Drone")
    description = models.TextField()
    rate_per_hour = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    rate_per_day = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    image = models.ImageField(upload_to='equipment/')

    # This boolean will let the owner toggle between "Available" and "Rented"
    is_available = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} - {self.owner.username}"

class EquipmentReview(models.Model):
    equipment = models.ForeignKey(Equipment, on_delete=models.CASCADE, related_name='reviews')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    rating = models.IntegerField(default=5)
    comment = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Review by {self.user.full_name} for {self.equipment.name}"


class NewsUpdate(models.Model):
    # Ensure you have an author field to track who posted it!
    author = models.ForeignKey(User, on_delete=models.CASCADE, null=True)
    title = models.CharField(max_length=200)
    content = models.TextField()

    # ADD THIS LINE FOR THE IMAGE:
    image = models.ImageField(upload_to='news/', null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title


class Notification(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    message = models.TextField()

    # THIS MUST SAY default=False
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Alert for {self.user.username}"