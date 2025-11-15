from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, Address, Notification


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """Custom User admin"""
    list_display = ['phone', 'name', 'email', 'is_kyc_verified', 'is_active', 'is_staff', 'created_at']
    list_filter = ['is_active', 'is_staff', 'is_superuser', 'is_kyc_verified', 'created_at']
    search_fields = ['phone', 'name', 'email', 'national_id', 'pan_no']
    ordering = ['-created_at']
    
    fieldsets = (
        (None, {'fields': ('phone', 'password')}),
        ('Personal info', {'fields': ('name', 'email', 'fcm_token', 'profile_picture')}),
        ('KYC Verification', {
            'fields': ('national_id', 'national_id_document', 'pan_no', 'pan_document', 'is_kyc_verified', 'kyc_submitted_at', 'kyc_verified_at'),
            'classes': ('collapse',)
        }),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login', 'date_joined', 'created_at', 'updated_at')}),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('phone', 'name', 'email', 'password1', 'password2'),
        }),
    )
    
    readonly_fields = ['created_at', 'updated_at', 'date_joined', 'last_login', 'kyc_submitted_at', 'kyc_verified_at']
    
    def save_model(self, request, obj, form, change):
        """Override save to set kyc_verified_at when is_kyc_verified is set to True"""
        if change and 'is_kyc_verified' in form.changed_data:
            if obj.is_kyc_verified and not obj.kyc_verified_at:
                from django.utils import timezone
                obj.kyc_verified_at = timezone.now()
            elif not obj.is_kyc_verified:
                obj.kyc_verified_at = None
        super().save_model(request, obj, form, change)


@admin.register(Address)
class AddressAdmin(admin.ModelAdmin):
    """Address admin"""
    list_display = ['user', 'title', 'full_name', 'city', 'state', 'is_default', 'created_at']
    list_filter = ['is_default', 'state', 'created_at']
    search_fields = ['user__name', 'user__phone', 'title', 'full_name', 'city']
    ordering = ['-is_default', '-created_at']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    """Notification admin"""
    list_display = ['user', 'title', 'type', 'is_read', 'created_at']
    list_filter = ['type', 'is_read', 'created_at']
    search_fields = ['user__name', 'user__phone', 'title', 'message']
    ordering = ['-created_at']
    readonly_fields = ['created_at']
