from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from core.models import User, Address
import json


class Store(models.Model):
    """Store model for vendors"""
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='stores')
    logo = models.ImageField(upload_to='store_logos/', blank=True, null=True)
    banner = models.ImageField(upload_to='store_banners/', blank=True, null=True)
    address = models.TextField(blank=True)
    latitude = models.DecimalField(max_digits=20, decimal_places=12, null=True, blank=True)
    longitude = models.DecimalField(max_digits=20, decimal_places=12, null=True, blank=True)
    phone = models.CharField(max_length=20)
    email = models.EmailField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    # Shipdaak warehouse fields
    shipdaak_pickup_warehouse_id = models.IntegerField(null=True, blank=True, help_text='Shipdaak pickup warehouse ID')
    shipdaak_rto_warehouse_id = models.IntegerField(null=True, blank=True, help_text='Shipdaak RTO warehouse ID')
    shipdaak_warehouse_created_at = models.DateTimeField(null=True, blank=True, help_text='When warehouse was created in Shipdaak')
    
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
    discount_type = models.CharField(max_length=10, choices=[('flat', 'Flat'), ('percentage', 'Percentage')], blank=True, null=True)
    discount = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True, validators=[MinValueValidator(0)])
    stock_quantity = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False)
    is_approved = models.BooleanField(default=False, help_text='Product must be approved by admin before it appears in app/web')
    variants = models.JSONField(default=dict, blank=True, help_text='Product variant data with enabled, variants, and combinations')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.name} - {self.store.name}"
    
    def get_variants_data(self):
        """Get variant data with default structure"""
        if not self.variants:
            return {
                "enabled": False,
                "variants": [],
                "combinations": {}
            }
        return self.variants
    
    def is_variants_enabled(self):
        """Check if product variants are enabled"""
        variants_data = self.get_variants_data()
        return variants_data.get("enabled", False)
    
    def get_total_stock(self):
        """Calculate total stock from variants if enabled, otherwise return stock_quantity"""
        if self.is_variants_enabled():
            variants_data = self.get_variants_data()
            combinations = variants_data.get("combinations", {})
            total = sum(
                int(combo.get("stock", 0))
                for combo in combinations.values()
                if isinstance(combo, dict)
            )
            return total
        return self.stock_quantity
    
    def save(self, *args, **kwargs):
        """Override save to auto-calculate stock and set price from primary combination when variants are enabled"""
        if self.is_variants_enabled():
            variants_data = self.get_variants_data()
            combinations = variants_data.get("combinations", {})
            
            # Find primary combination and set price from it
            primary_combination = None
            for combo_key, combo_data in combinations.items():
                if isinstance(combo_data, dict) and combo_data.get("is_primary", False):
                    primary_combination = combo_data
                    break
            
            if primary_combination and "price" in primary_combination:
                try:
                    self.price = primary_combination["price"]
                except (ValueError, TypeError):
                    pass  # Keep existing price if conversion fails
            
            # Auto-calculate stock from combinations
            total_stock = self.get_total_stock()
            self.stock_quantity = total_stock
        super().save(*args, **kwargs)
    
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
        ('accepted', 'Accepted'),
        ('rejected', 'Rejected'),
        ('shipped', 'Shipped'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled'),
        ('refunded', 'Refunded'),
    ]
    
    PAYMENT_METHOD_CHOICES = [
        ('cod', 'Cash on Delivery'),
        ('online', 'Online Payment'),  # SabPaisa
        ('phonepe', 'PhonePe Payment'),
    ]
    
    PAYMENT_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('success', 'Success'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='orders')
    merchant = models.ForeignKey(Store, on_delete=models.CASCADE, related_name='orders', null=True, blank=True, help_text='Store/vendor for this order')
    order_number = models.CharField(max_length=20, unique=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    subtotal = models.DecimalField(max_digits=10, decimal_places=2, default=0, help_text='Subtotal for this vendor\'s products')
    shipping_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0, help_text='Shipping cost for this order')
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    shipping_address = models.ForeignKey(Address, on_delete=models.SET_NULL, null=True, blank=True, related_name='shipping_orders', help_text='Shipping address for this order')
    billing_address = models.ForeignKey(Address, on_delete=models.SET_NULL, null=True, blank=True, related_name='billing_orders', help_text='Billing address for this order')
    phone = models.CharField(max_length=20)
    email = models.EmailField()
    notes = models.TextField(blank=True)
    payment_method = models.CharField(max_length=10, choices=PAYMENT_METHOD_CHOICES, default='cod')
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='pending')
    merchant_ready_date = models.DateTimeField(null=True, blank=True, help_text='When merchant accepts and marks ready')
    pickup_date = models.DateTimeField(null=True, blank=True, help_text='When order is picked up')
    delivered_date = models.DateTimeField(null=True, blank=True, help_text='When order is delivered')
    reject_reason = models.TextField(blank=True, null=True, help_text='Reason if merchant rejects')
    # Shipdaak shipment fields
    shipdaak_awb_number = models.CharField(max_length=50, blank=True, null=True, help_text='Shipdaak AWB/Tracking number')
    shipdaak_shipment_id = models.IntegerField(null=True, blank=True, help_text='Shipdaak shipment ID')
    shipdaak_order_id = models.IntegerField(null=True, blank=True, help_text='Shipdaak order ID')
    shipdaak_label_url = models.URLField(blank=True, null=True, help_text='Shipdaak shipping label URL')
    shipdaak_manifest_url = models.URLField(blank=True, null=True, help_text='Shipdaak manifest URL')
    shipdaak_status = models.CharField(max_length=50, blank=True, null=True, help_text='Current Shipdaak shipment status')
    shipdaak_courier_id = models.IntegerField(null=True, blank=True, help_text='Shipdaak courier ID used for shipment')
    shipdaak_courier_name = models.CharField(max_length=100, blank=True, null=True, help_text='Shipdaak courier name')
    # Package dimensions (set when merchant accepts order)
    package_length = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True, help_text='Package length in cm')
    package_breadth = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True, help_text='Package breadth in cm')
    package_height = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True, help_text='Package height in cm')
    package_weight = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True, help_text='Package weight in grams')
    commission_processed = models.BooleanField(default=False, help_text='Whether commission has been processed for this order')
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
    product_variant = models.CharField(max_length=255, blank=True, null=True, help_text='Selected product variant (e.g., "Size:Small,Color:Red")')
    
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


class GlobalCourier(models.Model):
    """Global courier configuration - all merchants see all active couriers"""
    courier_id = models.IntegerField(unique=True, help_text='Shipdaak courier ID')
    courier_name = models.CharField(max_length=100, help_text='Courier name')
    is_active = models.BooleanField(default=True, help_text='Whether this courier is active globally')
    priority = models.IntegerField(default=0, help_text='Priority order (lower = higher priority)')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.courier_name} (ID: {self.courier_id})"
    
    class Meta:
        ordering = ['priority', 'courier_name']
        verbose_name = 'Global Courier'
        verbose_name_plural = 'Global Couriers'


class Withdrawal(models.Model):
    """Withdrawal model for merchant withdrawal requests"""
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]
    
    merchant = models.ForeignKey(User, on_delete=models.CASCADE, related_name='withdrawals', limit_choices_to={'is_merchant': True})
    amount = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    # Bank account details
    bank_account_number = models.CharField(max_length=50, help_text='Bank account number')
    bank_ifsc = models.CharField(max_length=20, help_text='Bank IFSC code')
    bank_name = models.CharField(max_length=100, help_text='Bank name')
    account_holder_name = models.CharField(max_length=100, help_text='Account holder name')
    # PhonePe transaction fields (filled when withdrawal is processed)
    utr = models.CharField(max_length=100, blank=True, null=True, help_text='UTR from withdrawal processing')
    bank_id = models.CharField(max_length=20, blank=True, null=True, help_text='Bank ID if processed via PhonePe')
    vpa = models.CharField(max_length=100, blank=True, null=True, help_text='VPA if processed via PhonePe')
    rejection_reason = models.TextField(blank=True, null=True, help_text='Reason for rejection if status is rejected')
    processed_at = models.DateTimeField(blank=True, null=True, help_text='When withdrawal was processed')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.merchant.name} - ₹{self.amount} ({self.get_status_display()})"
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['merchant', '-created_at']),
            models.Index(fields=['status', '-created_at']),
        ]


class Banner(models.Model):
    """Banner model for promotional banners"""
    image = models.ImageField(upload_to='banners/', help_text='Banner image')
    title = models.CharField(max_length=200, help_text='Banner title')
    url = models.URLField(blank=True, null=True, help_text='URL to navigate when banner is clicked')
    is_active = models.BooleanField(default=True, help_text='Whether this banner is active')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.title} - {'Active' if self.is_active else 'Inactive'}"
    
    class Meta:
        ordering = ['-created_at']


class Popup(models.Model):
    """Popup model for app startup popups"""
    image = models.ImageField(upload_to='popups/', help_text='Popup image')
    title = models.CharField(max_length=200, help_text='Popup title')
    is_active = models.BooleanField(default=True, help_text='Whether this popup is active')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.title} - {'Active' if self.is_active else 'Inactive'}"
    
    class Meta:
        ordering = ['-created_at']