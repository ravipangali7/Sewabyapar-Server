from rest_framework import serializers
from .models import User, Address, Notification, Otp, UserPaymentMethod, Withdrawal


class UserSerializer(serializers.ModelSerializer):
    national_id_document_front = serializers.ImageField(read_only=True)
    national_id_document_back = serializers.ImageField(read_only=True)
    company_register_document = serializers.ImageField(read_only=True)
    merchant_agreement = serializers.FileField(read_only=True)
    
    class Meta:
        model = User
        fields = ['id', 'phone', 'name', 'email', 'country_code', 'country', 'fcm_token', 'profile_picture', 
                  'national_id', 'national_id_document_front', 'national_id_document_back', 'pan_no', 'pan_document',
                  'company_register_id', 'company_register_document', 'merchant_agreement',
                  'is_kyc_verified', 'kyc_submitted_at', 'kyc_verified_at', 'kyc_rejected_at', 'kyc_rejection_reason',
                  'is_merchant', 'is_driver', 'is_freeze', 'merchant_code', 'is_edit_access', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at', 'is_kyc_verified', 'kyc_verified_at', 
                           'kyc_rejected_at', 'kyc_rejection_reason', 'is_merchant', 'is_driver', 'merchant_code',
                           'national_id_document_front', 'national_id_document_back', 'pan_document', 'company_register_document', 'merchant_agreement']
        extra_kwargs = {
            'phone': {'required': True},
            'name': {'required': True},
            'email': {'required': False}
        }


class UserCreateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)
    password_confirm = serializers.CharField(write_only=True)
    
    class Meta:
        model = User
        fields = ['phone', 'name', 'email', 'country_code', 'country', 'password', 'password_confirm', 'fcm_token', 'profile_picture']
        extra_kwargs = {
            'phone': {'required': True},
            'name': {'required': True},
            'email': {'required': False},
            'country_code': {'required': True},
            'country': {'required': True}
        }
    
    def validate(self, attrs):
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError("Passwords don't match")
        
        # Validate country and country_code match
        country_code = attrs.get('country_code')
        country = attrs.get('country')
        
        if country_code == '+977' and country != 'Nepal':
            raise serializers.ValidationError({'country': 'Country must be Nepal when country code is +977'})
        if country_code == '+91' and country != 'India':
            raise serializers.ValidationError({'country': 'Country must be India when country code is +91'})
            
        return attrs
    
    def create(self, validated_data):
        validated_data.pop('password_confirm')
        password = validated_data.pop('password')
        user = User.objects.create_user(**validated_data)
        user.set_password(password)
        user.save()
        return user


class UserUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['name', 'email', 'country_code', 'country', 'fcm_token', 'profile_picture']
        extra_kwargs = {
            'name': {'required': False},
            'email': {'required': False}
        }
    
    def validate(self, attrs):
        # Validate country and country_code match if both are provided
        country_code = attrs.get('country_code')
        country = attrs.get('country')
        
        if country_code and country:
            if country_code == '+977' and country != 'Nepal':
                raise serializers.ValidationError({'country': 'Country must be Nepal when country code is +977'})
            if country_code == '+91' and country != 'India':
                raise serializers.ValidationError({'country': 'Country must be India when country code is +91'})
                
        return attrs


class AddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = Address
        fields = ['id', 'title', 'full_name', 'phone', 'address', 'city', 'state', 'zip_code', 'building_name', 'flat_no', 'landmark', 'latitude', 'longitude', 'is_default', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def create(self, validated_data):
        # Ensure only one default address per user
        if validated_data.get('is_default', False):
            Address.objects.filter(user=validated_data['user']).update(is_default=False)
        return super().create(validated_data)
    
    def update(self, instance, validated_data):
        # Ensure only one default address per user
        if validated_data.get('is_default', False):
            Address.objects.filter(user=instance.user).exclude(id=instance.id).update(is_default=False)
        return super().update(instance, validated_data)


class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = ['id', 'title', 'message', 'type', 'is_read', 'created_at']
        read_only_fields = ['id', 'created_at']


class SendOTPSerializer(serializers.Serializer):
    """Serializer for sending OTP"""
    phone = serializers.CharField(max_length=15)
    country_code = serializers.ChoiceField(choices=User.COUNTRY_CODE_CHOICES)
    country = serializers.ChoiceField(choices=User.COUNTRY_CHOICES)
    
    def validate_phone(self, value):
        if not value or len(value) < 10:
            raise serializers.ValidationError("Invalid phone number")
        return value.strip()


class VerifyOTPSerializer(serializers.Serializer):
    """Serializer for verifying OTP and registering user"""
    phone = serializers.CharField(max_length=15)
    country_code = serializers.ChoiceField(choices=User.COUNTRY_CODE_CHOICES)
    country = serializers.ChoiceField(choices=User.COUNTRY_CHOICES)
    otp = serializers.CharField(max_length=6)
    name = serializers.CharField(max_length=100)
    email = serializers.EmailField(required=False, allow_blank=True, allow_null=True)
    password = serializers.CharField(min_length=8)
    password_confirm = serializers.CharField(min_length=8)
    user_type = serializers.ChoiceField(choices=[('customer', 'Customer'), ('merchant', 'Merchant'), ('driver', 'Driver')], default='customer')
    
    def validate_phone(self, value):
        if not value or len(value) < 10:
            raise serializers.ValidationError("Invalid phone number")
        return value.strip()
    
    def validate_otp(self, value):
        if not value or len(value) != 6 or not value.isdigit():
            raise serializers.ValidationError("OTP must be a 6-digit number")
        return value
    
    def validate(self, attrs):
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError("Passwords don't match")
        
        # Validate country and country_code match
        country_code = attrs.get('country_code')
        country = attrs.get('country')
        
        if country_code == '+977' and country != 'Nepal':
            raise serializers.ValidationError({'country': 'Country must be Nepal when country code is +977'})
        if country_code == '+91' and country != 'India':
            raise serializers.ValidationError({'country': 'Country must be India when country code is +91'})
            
        return attrs


class ResendOTPSerializer(serializers.Serializer):
    """Serializer for resending OTP"""
    phone = serializers.CharField(max_length=15)
    country_code = serializers.ChoiceField(choices=User.COUNTRY_CODE_CHOICES)
    country = serializers.ChoiceField(choices=User.COUNTRY_CHOICES)
    
    def validate_phone(self, value):
        if not value or len(value) < 10:
            raise serializers.ValidationError("Invalid phone number")
        return value.strip()


class ForgotPasswordSendOTPSerializer(serializers.Serializer):
    """Serializer for sending OTP for password reset"""
    phone = serializers.CharField(max_length=15)
    country_code = serializers.ChoiceField(choices=User.COUNTRY_CODE_CHOICES)
    
    def validate_phone(self, value):
        if not value or len(value) < 10:
            raise serializers.ValidationError("Invalid phone number")
        return value.strip()


class ForgotPasswordVerifyOTPSerializer(serializers.Serializer):
    """Serializer for verifying OTP for password reset"""
    phone = serializers.CharField(max_length=15)
    country_code = serializers.ChoiceField(choices=User.COUNTRY_CODE_CHOICES)
    otp = serializers.CharField(max_length=6)
    
    def validate_phone(self, value):
        if not value or len(value) < 10:
            raise serializers.ValidationError("Invalid phone number")
        return value.strip()
    
    def validate_otp(self, value):
        if not value or len(value) != 6 or not value.isdigit():
            raise serializers.ValidationError("OTP must be a 6-digit number")
        return value


class ResetPasswordSerializer(serializers.Serializer):
    """Serializer for resetting password"""
    phone = serializers.CharField(max_length=15)
    country_code = serializers.ChoiceField(choices=User.COUNTRY_CODE_CHOICES)
    otp = serializers.CharField(max_length=6)
    new_password = serializers.CharField(min_length=8)
    password_confirm = serializers.CharField(min_length=8)
    
    def validate_phone(self, value):
        if not value or len(value) < 10:
            raise serializers.ValidationError("Invalid phone number")
        return value.strip()
    
    def validate_otp(self, value):
        if not value or len(value) != 6 or not value.isdigit():
            raise serializers.ValidationError("OTP must be a 6-digit number")
        return value
    
    def validate(self, attrs):
        if attrs['new_password'] != attrs['password_confirm']:
            raise serializers.ValidationError("Passwords don't match")
        return attrs


class DeleteAccountSerializer(serializers.Serializer):
    """Serializer for account deletion request"""
    # No additional fields needed since authentication token is sufficient
    pass


class UserUpgradeSerializer(serializers.Serializer):
    """Serializer for account upgrade"""
    upgrade_to = serializers.ChoiceField(choices=[('merchant', 'Merchant'), ('driver', 'Driver')])
    
    def validate(self, attrs):
        upgrade_to = attrs.get('upgrade_to')
        if upgrade_to not in ['merchant', 'driver']:
            raise serializers.ValidationError({'upgrade_to': 'Invalid upgrade option. Must be merchant or driver'})
        return attrs


class KYCSubmitSerializer(serializers.Serializer):
    """Serializer for KYC document submission"""
    national_id = serializers.CharField(max_length=50, required=False, allow_blank=True)
    national_id_document_front = serializers.ImageField(required=False, allow_null=True)
    national_id_document_back = serializers.ImageField(required=False, allow_null=True)
    pan_no = serializers.CharField(max_length=20, required=False, allow_blank=True)
    pan_document = serializers.ImageField(required=False, allow_null=True)
    company_register_id = serializers.CharField(max_length=50, required=False, allow_blank=True)
    company_register_document = serializers.ImageField(required=False, allow_null=True)
    merchant_agreement = serializers.FileField(required=False, allow_null=True)
    
    def validate(self, attrs):
        """Validate that at least some KYC information is provided"""
        has_national_id = attrs.get('national_id') or attrs.get('national_id_document_front') or attrs.get('national_id_document_back')
        has_pan = attrs.get('pan_no') or attrs.get('pan_document')
        has_company = attrs.get('company_register_id') or attrs.get('company_register_document')
        
        if not (has_national_id or has_pan):
            raise serializers.ValidationError('At least National ID or PAN information must be provided')
        
        # For merchants, company registration is optional but recommended
        return attrs


class KYCStatusSerializer(serializers.ModelSerializer):
    """Serializer for KYC status retrieval"""
    national_id_document_front = serializers.ImageField(read_only=True)
    national_id_document_back = serializers.ImageField(read_only=True)
    pan_document = serializers.ImageField(read_only=True)
    company_register_document = serializers.ImageField(read_only=True)
    merchant_agreement = serializers.FileField(read_only=True)
    
    class Meta:
        model = User
        fields = [
            'national_id', 'national_id_document_front', 'national_id_document_back',
            'pan_no', 'pan_document',
            'company_register_id', 'company_register_document',
            'merchant_agreement',
            'is_kyc_verified', 'kyc_submitted_at', 'kyc_verified_at',
            'kyc_rejected_at', 'kyc_rejection_reason'
        ]
        read_only_fields = [
            'is_kyc_verified', 'kyc_submitted_at', 'kyc_verified_at',
            'kyc_rejected_at', 'kyc_rejection_reason',
            'national_id_document_front', 'national_id_document_back',
            'pan_document', 'company_register_document', 'merchant_agreement'
        ]


class UserPaymentMethodSerializer(serializers.ModelSerializer):
    """Serializer for reading user payment methods"""
    user = UserSerializer(read_only=True)
    payment_method_type_display = serializers.CharField(source='get_payment_method_type_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    can_edit = serializers.SerializerMethodField()
    
    class Meta:
        model = UserPaymentMethod
        fields = ['id', 'user', 'payment_method_type', 'payment_method_type_display', 
                 'status', 'status_display', 'rejection_reason', 'payment_details',
                 'approved_at', 'rejected_at', 'can_edit', 'created_at', 'updated_at']
        read_only_fields = ['id', 'user', 'approved_at', 'rejected_at', 'created_at', 'updated_at']
    
    def get_can_edit(self, obj):
        """Return whether the payment method can be edited"""
        return obj.can_edit()


class UserPaymentMethodCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating user payment methods"""
    
    class Meta:
        model = UserPaymentMethod
        fields = ['payment_method_type', 'payment_details']
    
    def validate_payment_details(self, value):
        """Validate payment details based on payment method type"""
        payment_method_type = self.initial_data.get('payment_method_type')
        
        if not payment_method_type:
            raise serializers.ValidationError("Payment method type is required")
        
        if payment_method_type == 'bank_account':
            required_fields = ['account_number', 'ifsc', 'bank_name', 'account_holder_name']
            for field in required_fields:
                if field not in value or not value[field]:
                    raise serializers.ValidationError(f"{field.replace('_', ' ').title()} is required for bank account")
        
        elif payment_method_type == 'upi':
            required_fields = ['vpa']
            for field in required_fields:
                if field not in value or not value[field]:
                    raise serializers.ValidationError(f"{field.upper()} is required for UPI")
            if 'upi_id' not in value:
                value['upi_id'] = value.get('vpa', '')
        
        elif payment_method_type == 'wallet':
            required_fields = ['wallet_type', 'wallet_id']
            for field in required_fields:
                if field not in value or not value[field]:
                    raise serializers.ValidationError(f"{field.replace('_', ' ').title()} is required for wallet")
            if 'wallet_provider' not in value:
                value['wallet_provider'] = value.get('wallet_type', '')
        
        return value
    
    def create(self, validated_data):
        """Create payment method for the authenticated user"""
        user = self.context['request'].user
        
        # Check if payment method already exists
        if UserPaymentMethod.objects.filter(user=user).exists():
            raise serializers.ValidationError("Payment method already exists. Please update the existing one.")
        
        validated_data['user'] = user
        return super().create(validated_data)


class UserPaymentMethodUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating user payment methods (only if pending or rejected)"""
    
    class Meta:
        model = UserPaymentMethod
        fields = ['payment_method_type', 'payment_details']
    
    def validate(self, attrs):
        """Validate that payment method can be edited"""
        instance = self.instance
        if instance and not instance.can_edit():
            raise serializers.ValidationError("Cannot edit payment method that is already approved")
        return attrs
    
    def validate_payment_details(self, value):
        """Validate payment details based on payment method type"""
        payment_method_type = self.initial_data.get('payment_method_type') or (self.instance.payment_method_type if self.instance else None)
        
        if not payment_method_type:
            raise serializers.ValidationError("Payment method type is required")
        
        if payment_method_type == 'bank_account':
            required_fields = ['account_number', 'ifsc', 'bank_name', 'account_holder_name']
            for field in required_fields:
                if field not in value or not value[field]:
                    raise serializers.ValidationError(f"{field.replace('_', ' ').title()} is required for bank account")
        
        elif payment_method_type == 'upi':
            required_fields = ['vpa']
            for field in required_fields:
                if field not in value or not value[field]:
                    raise serializers.ValidationError(f"{field.upper()} is required for UPI")
            if 'upi_id' not in value:
                value['upi_id'] = value.get('vpa', '')
        
        elif payment_method_type == 'wallet':
            required_fields = ['wallet_type', 'wallet_id']
            for field in required_fields:
                if field not in value or not value[field]:
                    raise serializers.ValidationError(f"{field.replace('_', ' ').title()} is required for wallet")
            if 'wallet_provider' not in value:
                value['wallet_provider'] = value.get('wallet_type', '')
        
        return value
    
    def update(self, instance, validated_data):
        """Update payment method and reset status to pending if it was rejected"""
        if instance.status == 'rejected':
            validated_data['status'] = 'pending'
            validated_data['rejection_reason'] = None
            validated_data['rejected_at'] = None
        
        return super().update(instance, validated_data)


class WithdrawalSerializer(serializers.ModelSerializer):
    merchant = UserSerializer(read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    payment_method = serializers.SerializerMethodField()
    payment_details = serializers.SerializerMethodField()
    
    class Meta:
        model = Withdrawal
        fields = ['id', 'merchant', 'amount', 'status', 'status_display', 
                 'payment_method', 'payment_details', 'rejection_reason', 
                 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_payment_method(self, obj):
        """Get payment method details"""
        if obj.payment_method:
            return {
                'id': obj.payment_method.id,
                'payment_method_type': obj.payment_method.payment_method_type,
                'payment_method_type_display': obj.payment_method.get_payment_method_type_display(),
                'status': obj.payment_method.status,
                'status_display': obj.payment_method.get_status_display(),
            }
        return None
    
    def get_payment_details(self, obj):
        """Get payment details from payment_method"""
        if obj.payment_method and obj.payment_method.payment_details:
            return obj.payment_method.payment_details
        return None


class WithdrawalCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating withdrawal requests - only requires amount"""
    
    class Meta:
        model = Withdrawal
        fields = ['amount']
    
    def validate_amount(self, value):
        """Validate withdrawal amount"""
        if value <= 0:
            raise serializers.ValidationError("Withdrawal amount must be greater than 0")
        return value