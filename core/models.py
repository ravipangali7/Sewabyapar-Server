from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator, MaxValueValidator


class UserManager(BaseUserManager):
    """Custom user manager for phone-based authentication"""
    
    def create_user(self, phone, name, password=None, email=None, country_code='+91', country='India', **extra_fields):
        """Create and return a regular user with phone as username"""
        if not phone:
            raise ValueError('The phone field must be set')
        if not name:
            raise ValueError('The name field must be set')
            
        if email:
            email = self.normalize_email(email)
        user = self.model(
            phone=phone,
            email=email,
            name=name,
            country_code=country_code,
            country=country,
            username=phone,  # Set username to phone
            **extra_fields
        )
        user.set_password(password)
        user.save(using=self._db)
        return user
    
    def create_superuser(self, phone, name, password=None, email=None, country_code='+91', country='India', **extra_fields):
        """Create and return a superuser with phone as username"""
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)
        
        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')
            
        return self.create_user(phone, name, password, email, country_code, country, **extra_fields)


class User(AbstractUser):
    """Custom User model with phone number as username"""
    COUNTRY_CODE_CHOICES = [
        ('+977', '+977'),
        ('+91', '+91'),
    ]
    
    COUNTRY_CHOICES = [
        ('Nepal', 'Nepal'),
        ('India', 'India'),
    ]
    
    phone = models.CharField(max_length=15, unique=True)
    name = models.CharField(max_length=100)
    email = models.EmailField(blank=True, null=True)
    country_code = models.CharField(max_length=5, choices=COUNTRY_CODE_CHOICES, default='+91')
    country = models.CharField(max_length=10, choices=COUNTRY_CHOICES, default='India')
    fcm_token = models.CharField(max_length=255, blank=True, null=True)
    profile_picture = models.ImageField(upload_to='profile_pictures/', blank=True, null=True)
    
    # KYC Verification Fields
    national_id = models.CharField(max_length=50, blank=True, null=True, help_text='National ID number')
    national_id_document_front = models.ImageField(upload_to='kyc_documents/', blank=True, null=True, help_text='National ID document front image')
    national_id_document_back = models.ImageField(upload_to='kyc_documents/', blank=True, null=True, help_text='National ID document back image')
    pan_no = models.CharField(max_length=20, blank=True, null=True, help_text='PAN (Permanent Account Number)')
    pan_document = models.ImageField(upload_to='kyc_documents/', blank=True, null=True, help_text='PAN document image')
    # Merchant-specific KYC fields
    company_register_id = models.CharField(max_length=50, blank=True, null=True, help_text='Company registration ID (for merchants only)')
    company_register_document = models.ImageField(upload_to='kyc_documents/', blank=True, null=True, help_text='Company registration document (for merchants only)')
    merchant_agreement = models.FileField(upload_to='kyc_documents/', blank=True, null=True, help_text='Signed merchant agreement PDF document (for merchants only)')
    is_kyc_verified = models.BooleanField(default=False, help_text='Whether KYC has been verified by admin')
    kyc_submitted_at = models.DateTimeField(blank=True, null=True, help_text='When user submitted KYC information')
    kyc_verified_at = models.DateTimeField(blank=True, null=True, help_text='When KYC was verified by admin')
    kyc_rejected_at = models.DateTimeField(blank=True, null=True, help_text='When KYC was rejected by admin')
    kyc_rejection_reason = models.TextField(blank=True, null=True, help_text='Reason for KYC rejection')
    
    # Merchant/Driver Role Fields
    is_merchant = models.BooleanField(default=False, help_text='Whether user is a merchant/seller')
    is_driver = models.BooleanField(default=False, help_text='Whether user is a driver')
    
    # Balance field
    balance = models.DecimalField(max_digits=10, decimal_places=2, default=0, 
                                  validators=[MinValueValidator(0)],
                                  help_text='User balance')
    
    # Freeze field
    is_freeze = models.BooleanField(default=False, help_text='Whether user account is frozen')
    
    # Merchant code field
    merchant_code = models.CharField(max_length=50, null=True, blank=True, unique=True, help_text='Auto-generated merchant code (e.g., MSB1, MSB2) - only for merchants')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Remove first_name and last_name from required fields
    first_name = None
    last_name = None
    
    # Use custom manager
    objects = UserManager()
    
    USERNAME_FIELD = 'phone'
    REQUIRED_FIELDS = ['name']
    
    def clean(self):
        """Validate that country and country_code match, and merchant/driver exclusivity"""
        super().clean()
        if self.country_code == '+977' and self.country != 'Nepal':
            raise ValidationError({'country': 'Country must be Nepal when country code is +977'})
        if self.country_code == '+91' and self.country != 'India':
            raise ValidationError({'country': 'Country must be India when country code is +91'})
        
        # Ensure merchant and driver can't both be True
        if self.is_merchant and self.is_driver:
            raise ValidationError({
                'is_merchant': 'User cannot be both merchant and driver at the same time',
                'is_driver': 'User cannot be both merchant and driver at the same time'
            })
    
    def save(self, *args, **kwargs):
        # Validate before saving
        self.full_clean()
        # Set username to phone number
        self.username = self.phone
        # Auto-set country based on country_code if not already set
        if self.country_code == '+977' and not self.country:
            self.country = 'Nepal'
        elif self.country_code == '+91' and not self.country:
            self.country = 'India'
        
        # Generate merchant_code if user is a merchant and code is not set
        if self.is_merchant and not self.merchant_code:
            # Find the highest existing code number
            max_code_number = 0
            existing_merchants = User.objects.filter(is_merchant=True).exclude(merchant_code__isnull=True).filter(merchant_code__startswith='MSB')
            for merchant in existing_merchants:
                if merchant.merchant_code and merchant.merchant_code.startswith('MSB'):
                    try:
                        # Extract number after "MSB" prefix (3 characters)
                        num = int(merchant.merchant_code[3:])
                        if num > max_code_number:
                            max_code_number = num
                    except ValueError:
                        pass  # Ignore codes that don't match the pattern
            
            # Generate new code with zero-padding
            new_number = max_code_number + 1
            code = f"MSB{new_number:02d}"
            # Ensure uniqueness
            while User.objects.filter(merchant_code=code).exists():
                new_number += 1
                code = f"MSB{new_number:02d}"
            self.merchant_code = code
        elif not self.is_merchant:
            # Clear merchant_code if user is not a merchant
            self.merchant_code = None
        
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.name} ({self.phone})"
    
    class Meta:
        ordering = ['-created_at']


class Address(models.Model):
    """User address model"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='addresses')
    title = models.CharField(max_length=50)  # e.g., "Home", "Office"
    full_name = models.CharField(max_length=100)
    phone = models.CharField(max_length=20)
    address = models.TextField()
    city = models.CharField(max_length=50)
    state = models.CharField(max_length=50)
    zip_code = models.CharField(max_length=10)
    building_name = models.CharField(max_length=100, blank=True, null=True)
    flat_no = models.CharField(max_length=50, blank=True, null=True)
    landmark = models.CharField(max_length=200, blank=True, null=True)
    latitude = models.DecimalField(max_digits=20, decimal_places=12, null=True, blank=True)
    longitude = models.DecimalField(max_digits=20, decimal_places=12, null=True, blank=True)
    is_default = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.user.name} - {self.title}"
    
    class Meta:
        ordering = ['-is_default', '-created_at']
        verbose_name_plural = "Addresses"


class Otp(models.Model):
    """OTP model for phone verification"""
    phone = models.CharField(max_length=15)
    otp = models.CharField(max_length=6)
    country_code = models.CharField(max_length=5, choices=User.COUNTRY_CODE_CHOICES)
    expires_at = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    def is_expired(self):
        """Check if OTP has expired"""
        from django.utils import timezone
        return timezone.now() > self.expires_at
    
    def __str__(self):
        return f"OTP for {self.phone}"
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['phone']),
        ]


class Notification(models.Model):
    """User notification model"""
    NOTIFICATION_TYPES = [
        ('order', 'Order'),
        ('promotion', 'Promotion'),
        ('security', 'Security'),
        ('general', 'General'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    title = models.CharField(max_length=200)
    message = models.TextField()
    type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES, default='general')
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.user.name} - {self.title}"
    
    class Meta:
        ordering = ['-created_at']


class SuperSetting(models.Model):
    """Super Setting model for platform-wide configuration"""
    sales_commission = models.DecimalField(max_digits=5, decimal_places=2, default=0,
                                          validators=[MinValueValidator(0), MaxValueValidator(100)],
                                          help_text='Sales commission percentage')
    basic_shipping_charge = models.DecimalField(max_digits=10, decimal_places=2, default=0,
                                               validators=[MinValueValidator(0)],
                                               help_text='Basic shipping charge per vendor')
    balance = models.DecimalField(max_digits=10, decimal_places=2, default=0,
                                 validators=[MinValueValidator(0)],
                                 help_text='Platform balance')
    merchant_agreement_file = models.FileField(upload_to='merchant_agreements/', blank=True, null=True,
                                               help_text='Merchant agreement file for download')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Super Setting"
        verbose_name_plural = "Super Settings"
    
    def save(self, *args, **kwargs):
        # Ensure only one instance exists
        if not self.pk and SuperSetting.objects.exists():
            raise ValueError("Only one SuperSetting instance is allowed")
        super().save(*args, **kwargs)
    
    def __str__(self):
        return "Super Setting"


class Transaction(models.Model):
    """Transaction model to track all financial transactions"""
    TRANSACTION_TYPE_CHOICES = [
        ('commission', 'Commission'),
        ('withdrawal', 'Withdrawal Request'),
        ('withdrawal_processed', 'Withdrawal Processed'),
        ('phonepe_payment', 'PhonePe Payment'),
        ('payout', 'Merchant Payout'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='transactions')
    transaction_type = models.CharField(max_length=30, choices=TRANSACTION_TYPE_CHOICES)
    amount = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    description = models.TextField(blank=True, help_text='Transaction description')
    related_order = models.ForeignKey('ecommerce.Order', on_delete=models.SET_NULL, null=True, blank=True, related_name='transactions', help_text='Related order for commission/payout/phonepe transactions')
    related_withdrawal = models.ForeignKey('ecommerce.Withdrawal', on_delete=models.SET_NULL, null=True, blank=True, related_name='transactions', help_text='Related withdrawal for withdrawal transactions')
    # PhonePe transaction fields
    merchant_order_id = models.CharField(max_length=100, blank=True, null=True, help_text='Merchant Order ID for PhonePe payment callbacks', db_index=True)
    utr = models.CharField(max_length=100, blank=True, null=True, help_text='Unique Transaction Reference (UTR) for PhonePe transactions')
    bank_id = models.CharField(max_length=20, blank=True, null=True, help_text='Bank ID for PhonePe transactions')
    vpa = models.CharField(max_length=100, blank=True, null=True, help_text='Virtual Payment Address (VPA) for PhonePe transactions')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.user.name} - {self.get_transaction_type_display()} - ₹{self.amount} ({self.get_status_display()})"
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['transaction_type', '-created_at']),
            models.Index(fields=['merchant_order_id']),
        ]