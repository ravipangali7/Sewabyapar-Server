from django.contrib import admin
from .models import (
    Store, Category, Product, ProductImage, Cart, Order, OrderItem, 
    Review, Wishlist, Coupon, GlobalCourier, ShippingChargeHistory,
    MerchantPaymentSetting
)


@admin.register(Store)
class StoreAdmin(admin.ModelAdmin):
    list_display = ['name', 'owner', 'email', 'phone', 'is_active', 'is_opened', 'minimum_order_value', 'shipdaak_pickup_warehouse_id', 'created_at']
    list_filter = ['is_active', 'is_opened', 'created_at']
    search_fields = ['name', 'owner__username', 'email']
    readonly_fields = ['created_at', 'updated_at', 'shipdaak_pickup_warehouse_id', 
                      'shipdaak_rto_warehouse_id', 'shipdaak_warehouse_created_at']
    fieldsets = (
        ('Store Information', {
            'fields': ('name', 'description', 'owner', 'logo', 'banner')
        }),
        ('Contact Information', {
            'fields': ('phone', 'email', 'address', 'latitude', 'longitude')
        }),
        ('Shipping Settings', {
            'fields': ('minimum_order_value',)
        }),
        ('Status', {
            'fields': ('is_active', 'is_opened')
        }),
        ('Shipdaak Integration', {
            'fields': ('shipdaak_pickup_warehouse_id', 'shipdaak_rto_warehouse_id', 'shipdaak_warehouse_created_at'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'parent', 'is_active', 'created_at']
    list_filter = ['is_active', 'parent', 'created_at']
    search_fields = ['name', 'description']
    readonly_fields = ['created_at']


class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['name', 'store', 'category', 'price', 'stock_quantity', 'is_active', 'is_featured', 'created_at']
    list_filter = ['is_active', 'is_featured', 'category', 'store', 'created_at']
    search_fields = ['name', 'description', 'sku', 'store__name']
    readonly_fields = ['created_at', 'updated_at']
    inlines = [ProductImageInline]


@admin.register(ProductImage)
class ProductImageAdmin(admin.ModelAdmin):
    list_display = ['product', 'is_primary', 'created_at']
    list_filter = ['is_primary', 'created_at']


@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ['user', 'product', 'quantity', 'created_at']
    list_filter = ['created_at']
    search_fields = ['user__username', 'product__name']


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ['total']


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['order_number', 'user', 'status', 'total_amount', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['order_number', 'user__username', 'email']
    readonly_fields = ['order_number', 'created_at', 'updated_at']
    inlines = [OrderItemInline]


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ['order', 'product', 'store', 'quantity', 'price', 'total', 'product_variant']
    list_filter = ['store', 'order__status']
    search_fields = ['product__name', 'product_variant']


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ['user', 'product', 'rating', 'is_verified_purchase', 'created_at']
    list_filter = ['rating', 'is_verified_purchase', 'created_at']
    search_fields = ['user__username', 'product__name', 'title']


@admin.register(Wishlist)
class WishlistAdmin(admin.ModelAdmin):
    list_display = ['user', 'product', 'created_at']
    list_filter = ['created_at']
    search_fields = ['user__username', 'product__name']


@admin.register(Coupon)
class CouponAdmin(admin.ModelAdmin):
    list_display = ['code', 'discount_type', 'discount_value', 'is_active', 'valid_from', 'valid_until', 'used_count']
    list_filter = ['discount_type', 'is_active', 'valid_from', 'valid_until']
    search_fields = ['code', 'description']
    readonly_fields = ['used_count', 'created_at']


@admin.register(GlobalCourier)
class GlobalCourierAdmin(admin.ModelAdmin):
    list_display = ['courier_name', 'courier_id', 'is_active', 'priority', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['courier_name', 'courier_id']
    readonly_fields = ['created_at', 'updated_at']
    list_editable = ['is_active', 'priority']


@admin.register(ShippingChargeHistory)
class ShippingChargeHistoryAdmin(admin.ModelAdmin):
    list_display = ['order', 'merchant', 'customer', 'shipping_charge', 'courier_rate', 'commission', 'paid_by', 'created_at']
    list_filter = ['paid_by', 'created_at']
    search_fields = ['order__order_number', 'merchant__name', 'customer__name']
    readonly_fields = ['created_at']
    ordering = ['-created_at']


@admin.register(MerchantPaymentSetting)
class MerchantPaymentSettingAdmin(admin.ModelAdmin):
    list_display = ['user', 'payment_method_type', 'status', 'rejection_reason', 'created_at', 'approved_at', 'rejected_at']
    list_filter = ['status', 'payment_method_type', 'created_at', 'approved_at', 'rejected_at']
    search_fields = ['user__username', 'user__name', 'user__email', 'rejection_reason']
    readonly_fields = ['created_at', 'updated_at', 'approved_at', 'rejected_at']
    fieldsets = (
        ('Merchant Information', {
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
