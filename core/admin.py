from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, Address, Notification, SuperSetting, UserPaymentMethod, Withdrawal, Agent


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """Custom User admin"""
    list_display = ['phone', 'name', 'email', 'is_merchant', 'is_driver', 'is_kyc_verified', 'balance', 'is_active', 'is_freeze', 'is_staff', 'created_at']
    list_filter = ['is_active', 'is_staff', 'is_superuser', 'is_merchant', 'is_driver', 'is_kyc_verified', 'is_freeze', 'created_at']
    search_fields = ['phone', 'name', 'email', 'national_id', 'pan_no']
    ordering = ['-created_at']


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


@admin.register(SuperSetting)
class SuperSettingAdmin(admin.ModelAdmin):
    """SuperSetting admin"""
    list_display = ['sales_commission', 'shipping_charge_commission', 'travel_ticket_percentage', 'balance', 'created_at', 'updated_at']
    fields = ['sales_commission', 'shipping_charge_commission', 'travel_ticket_percentage', 'balance', 'created_at', 'updated_at']
    readonly_fields = ['created_at', 'updated_at']
    
    def has_add_permission(self, request):
        # Only allow one SuperSetting instance
        if SuperSetting.objects.exists():
            return False
        return super().has_add_permission(request)
    
    def has_delete_permission(self, request, obj=None):
        # Prevent deletion of SuperSetting
        return False


@admin.register(UserPaymentMethod)
class UserPaymentMethodAdmin(admin.ModelAdmin):
    """UserPaymentMethod admin"""
    list_display = ['user', 'payment_method_type', 'status', 'rejection_reason', 'created_at', 'approved_at', 'rejected_at']
    list_filter = ['status', 'payment_method_type', 'created_at', 'approved_at', 'rejected_at']
    search_fields = ['user__username', 'user__name', 'user__email', 'rejection_reason']
    readonly_fields = ['created_at', 'updated_at', 'approved_at', 'rejected_at']
    fieldsets = (
        ('User Information', {
            'fields': ('user',)
        }),
        ('Payment Method', {
            'fields': ('payment_method_type', 'payment_details')
        }),
        ('Verification Status', {
            'fields': ('status', 'rejection_reason')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'approved_at', 'rejected_at'),
            'classes': ('collapse',)
        }),
    )
    ordering = ['-created_at']


@admin.register(Withdrawal)
class WithdrawalAdmin(admin.ModelAdmin):
    """Withdrawal admin"""
    list_display = ['id', 'merchant', 'amount', 'status', 'payment_method', 'created_at', 'updated_at']
    list_filter = ['status', 'created_at', 'updated_at']
    search_fields = ['merchant__name', 'merchant__phone', 'merchant__email', 'id', 'rejection_reason']
    readonly_fields = ['created_at', 'updated_at']
    fieldsets = (
        ('Withdrawal Information', {
            'fields': ('merchant', 'amount', 'status', 'payment_method')
        }),
        ('Rejection Information', {
            'fields': ('rejection_reason',),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    ordering = ['-created_at']


@admin.register(Agent)
class AgentAdmin(admin.ModelAdmin):
    """Agent admin"""
    list_display = ['user', 'dealer', 'commission_type', 'commission_value', 'is_active', 'created_at']
    list_filter = ['is_active', 'commission_type', 'created_at']
    search_fields = ['user__name', 'user__phone', 'dealer__user__name']
    readonly_fields = ['created_at', 'updated_at']
    filter_horizontal = ['committees']
