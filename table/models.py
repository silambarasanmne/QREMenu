from django.db import models
from django.contrib.auth.models import User

class Restaurant(models.Model):
    restaurant_id = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=255)
    logo = models.ImageField(upload_to='RestaurantLogo/', blank=True, null=True)
    phone = models.CharField(max_length=20, blank=True, default='')
    address = models.TextField(blank=True, default='')
    table_count = models.PositiveIntegerField(default=10)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} [{self.restaurant_id}]"

# UserProfile for SaaS Role-Based Access Control (RBAC)
class UserProfile(models.Model):
    ROLE_CHOICES = [
        ('KITCHEN', 'Kitchen Staff'),
        ('WAITER', 'Staff / Waiter'),
        ('RESTAURANT_ADMIN', 'Restaurant Admin'),
        ('SUPER_ADMIN', 'Super Admin'),
    ]
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    restaurant_id = models.CharField(max_length=50, default='R001')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='WAITER')

    def __str__(self):
        return f"{self.user.username} ({self.role} @ {self.restaurant_id})"

class Category(models.Model):
    restaurant_id = models.CharField(max_length=50, default='R001')
    name = models.CharField(max_length=255)
    image = models.ImageField(upload_to='Category/')
    
    def __str__(self):
        return f"{self.name} [{self.restaurant_id}]"

class FoodItem(models.Model):
    restaurant_id = models.CharField(max_length=50, default='R001')
    name = models.CharField(max_length=255)
    category = models.ForeignKey(Category, related_name='food_items', on_delete=models.CASCADE)
    description = models.TextField(blank=True, default='')
    image = models.ImageField(upload_to='FoodItem/', blank=True, null=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    is_available = models.BooleanField(default=True)
    display_order = models.IntegerField(default=0)

    def __str__(self):
        return f"{self.name} (₹{self.price})"

# Model to store food items that are not submitted
class NotSubmittedItem(models.Model):
    restaurant_id = models.CharField(max_length=50, default='R001')
    food_item = models.ForeignKey(FoodItem, on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    image = models.ImageField(upload_to='NotSubmitted/')
    tableNumber = models.PositiveIntegerField(default=0)
    quantity = models.PositiveIntegerField(default=1)

    def __str__(self):
        return f"Table {self.tableNumber}: {self.name} x{self.quantity}"

# Model to store submitted food items for kitchen & billing
class SubmittedItem(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending / New'),
        ('confirmed', 'Preparing'),
        ('ready', 'Ready to Serve'),
        ('served', 'Served'),
        ('completed', 'Completed'),
    ]

    PAYMENT_STATUS_CHOICES = [
        ('unpaid', 'Unpaid'),
        ('paid', 'Paid'),
    ]

    PAYMENT_METHOD_CHOICES = [
        ('none', 'None'),
        ('cash', 'Cash'),
        ('upi', 'Hotel UPI QR'),
    ]

    restaurant_id = models.CharField(max_length=50, default='R001')
    food_item = models.ForeignKey('FoodItem', on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    image = models.ImageField(upload_to='Submitted/')
    quantity = models.PositiveIntegerField(default=1)
    total_price = models.DecimalField(max_digits=10, decimal_places=2, blank=True)
    tableNumber = models.PositiveIntegerField(default=0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='unpaid')
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES, default='none')
    order_round = models.PositiveIntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        self.total_price = self.price * self.quantity
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Table {self.tableNumber}: {self.name} x{self.quantity} [{self.status}]"

class orders(models.Model):
    restaurant_id = models.CharField(max_length=50, default='R001')
    tableNumber = models.PositiveIntegerField(default=0)
    name = models.CharField(max_length=255)
    quantity = models.PositiveIntegerField(default=1)
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=[('pending', 'Pending'), ('confirmed', 'Confirmed')], default='pending')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Order Table {self.tableNumber}: {self.name} x{self.quantity}"
