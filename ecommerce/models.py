from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from core.models import User


class Store(models.Model):
    """Store model for vendors"""
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='stores')
    logo = models.ImageField(upload_to='store_logos/', blank=True, null=True)
    banner = models.ImageField(upload_to='store_banners/', blank=True, null=True)
    address = models.TextField()
    phone = models.CharField(max_length=20)
    email = models.EmailField()
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.name
    
    class Meta:
        ordering = ['-created_at']


class Category(models.Model):
    """Product category model"""
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    image = models.ImageField(upload_to='categories/', blank=True, null=True)
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='subcategories')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name_plural = "Categories"
        ordering = ['name']


class Product(models.Model):
    """Product model"""
    name = models.CharField(max_length=200)
    description = models.TextField()
    store = models.ForeignKey(Store, on_delete=models.CASCADE, related_name='products')
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='products')
    price = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    compare_price = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True, validators=[MinValueValidator(0)])
    sku = models.CharField(max_length=100, unique=True)
    stock_quantity = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False)
    weight = models.DecimalField(max_digits=8, decimal_places=2, blank=True, null=True, validators=[MinValueValidator(0)])
    dimensions = models.CharField(max_length=50, blank=True)  # e.g., "10x5x3 inches"
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.name} - {self.store.name}"
    
    class Meta:
        ordering = ['-created_at']


class ProductImage(models.Model):
    """Product images model"""
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='products/')
    alt_text = models.CharField(max_length=200, blank=True)
    is_primary = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.product.name} - Image {self.id}"
    
    class Meta:
        ordering = ['is_primary', '-created_at']


class Cart(models.Model):
    """Shopping cart model"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='cart')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1, validators=[MinValueValidator(1)])
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.user.name} - {self.product.name} x{self.quantity}"
    
    class Meta:
        unique_together = ['user', 'product']


class Order(models.Model):
    """Order model"""
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('processing', 'Processing'),
        ('shipped', 'Shipped'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled'),
        ('refunded', 'Refunded'),
    ]
    
    PAYMENT_METHOD_CHOICES = [
        ('cod', 'Cash on Delivery'),
        ('online', 'Online Payment'),
    ]
    
    PAYMENT_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('success', 'Success'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='orders')
    order_number = models.CharField(max_length=20, unique=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    shipping_address = models.TextField()
    billing_address = models.TextField()
    phone = models.CharField(max_length=20)
    email = models.EmailField()
    notes = models.TextField(blank=True)
    payment_method = models.CharField(max_length=10, choices=PAYMENT_METHOD_CHOICES, default='cod')
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='pending')
    # PhonePe Transaction Details
    phonepe_transaction_id = models.CharField(max_length=100, blank=True, null=True, help_text='PhonePe Transaction ID (OM...)')
    phonepe_order_id = models.CharField(max_length=100, blank=True, null=True, help_text='PhonePe Order ID (OMO...)')
    phonepe_merchant_order_id = models.CharField(max_length=100, blank=True, null=True, help_text='Merchant Reference ID')
    phonepe_transaction_date = models.DateTimeField(blank=True, null=True, help_text='PhonePe Transaction Date/Time')
    phonepe_processing_mechanism = models.CharField(max_length=50, blank=True, null=True, help_text='Processing Mechanism (e.g., UPI)')
    phonepe_product_type = models.CharField(max_length=50, blank=True, null=True, help_text='Product Type (e.g., PhonePe PG)')
    phonepe_instrument_type = models.CharField(max_length=50, blank=True, null=True, help_text='Instrument Type (e.g., UPI)')
    phonepe_payment_mode = models.CharField(max_length=50, blank=True, null=True, help_text='Payment Mode (e.g., Bank Account)')
    phonepe_bank_id = models.CharField(max_length=20, blank=True, null=True, help_text='Bank ID (e.g., SBIN)')
    phonepe_card_network = models.CharField(max_length=50, blank=True, null=True, help_text='Card Network (e.g., UNKNOWN)')
    phonepe_utr = models.CharField(max_length=100, blank=True, null=True, help_text='Unique Transaction Reference from PhonePe')
    phonepe_vpa = models.CharField(max_length=100, blank=True, null=True, help_text='Virtual Payment Address from PhonePe')
    phonepe_transaction_note = models.TextField(blank=True, null=True, help_text='Transaction Note from PhonePe')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Order {self.order_number} - {self.user.name}"
    
    class Meta:
        ordering = ['-created_at']


class OrderItem(models.Model):
    """Order items model"""
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    store = models.ForeignKey(Store, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)  # Price at time of order
    total = models.DecimalField(max_digits=10, decimal_places=2)
    
    def __str__(self):
        return f"{self.order.order_number} - {self.product.name}"
    
    class Meta:
        ordering = ['id']


class Review(models.Model):
    """Product review model"""
    RATING_CHOICES = [
        (1, '1 Star'),
        (2, '2 Stars'),
        (3, '3 Stars'),
        (4, '4 Stars'),
        (5, '5 Stars'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reviews')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='reviews')
    rating = models.IntegerField(choices=RATING_CHOICES, validators=[MinValueValidator(1), MaxValueValidator(5)])
    title = models.CharField(max_length=200, blank=True, default='')
    comment = models.TextField()
    is_verified_purchase = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.user.name} - {self.product.name} ({self.rating} stars)"
    
    class Meta:
        unique_together = ['user', 'product']
        ordering = ['-created_at']


class Wishlist(models.Model):
    """Wishlist model"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='wishlist')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.user.name} - {self.product.name}"
    
    class Meta:
        unique_together = ['user', 'product']
        ordering = ['-created_at']


class Coupon(models.Model):
    """Coupon model"""
    code = models.CharField(max_length=20, unique=True)
    description = models.TextField(blank=True)
    discount_type = models.CharField(max_length=10, choices=[('percentage', 'Percentage'), ('fixed', 'Fixed Amount')])
    discount_value = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    minimum_amount = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True, validators=[MinValueValidator(0)])
    usage_limit = models.PositiveIntegerField(blank=True, null=True)
    used_count = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    valid_from = models.DateTimeField()
    valid_until = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.code
    
    def is_valid(self):
        now = timezone.now()
        return (self.is_active and 
                self.valid_from <= now <= self.valid_until and
                (self.usage_limit is None or self.used_count < self.usage_limit))
    
    class Meta:
        ordering = ['-created_at']
