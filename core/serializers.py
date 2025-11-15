from rest_framework import serializers
from .models import User, Address, Notification, Otp


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'phone', 'name', 'email', 'country_code', 'country', 'fcm_token', 'profile_picture', 
                  'national_id', 'pan_no', 'is_kyc_verified', 'kyc_submitted_at', 'kyc_verified_at', 
                  'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at', 'is_kyc_verified', 'kyc_verified_at']
        extra_kwargs = {
            'phone': {'required': True},
            'name': {'required': True},
            'email': {'required': True}
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
        fields = ['id', 'title', 'full_name', 'phone', 'address', 'city', 'state', 'zip_code', 'latitude', 'longitude', 'is_default', 'created_at', 'updated_at']
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
    password = serializers.CharField(min_length=8)
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