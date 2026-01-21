from rest_framework import serializers
from decimal import Decimal
from .models import (
    Store, Category, Product, ProductImage, Cart, Order, OrderItem, 
    Review, Wishlist, Coupon, Withdrawal, Banner, Popup, MerchantPaymentSetting,
    ShippingChargeHistory
)
from core.models import Transaction
from core.serializers import UserSerializer, AddressSerializer


class StoreSerializer(serializers.ModelSerializer):
    owner = UserSerializer(read_only=True)
    
    class Meta:
        model = Store
        fields = ['id', 'name', 'description', 'owner', 'logo', 'banner', 'address', 
                 'latitude', 'longitude', 'phone', 'email', 'is_active', 'is_opened',
                 'minimum_order_value',
                 'shipdaak_pickup_warehouse_id', 'shipdaak_rto_warehouse_id', 
                 'shipdaak_warehouse_created_at', 'created_at', 'updated_at']
        read_only_fields = ['id', 'is_opened', 'shipdaak_pickup_warehouse_id', 'shipdaak_rto_warehouse_id', 
                          'shipdaak_warehouse_created_at', 'created_at', 'updated_at']
    
    def to_representation(self, instance):
        data = super().to_representation(instance)
        request = self.context.get('request')
        
        # Convert logo and banner to full URLs
        if instance.logo and request:
            data['logo'] = request.build_absolute_uri(instance.logo.url)
        if instance.banner and request:
            data['banner'] = request.build_absolute_uri(instance.banner.url)
        
        return data


class CategorySerializer(serializers.ModelSerializer):
    subcategories = serializers.SerializerMethodField()
    image = serializers.SerializerMethodField()
    
    class Meta:
        model = Category
        fields = ['id', 'name', 'description', 'image', 'parent', 'subcategories', 
                 'is_active', 'created_at']
        read_only_fields = ['id', 'created_at']
    
    def get_image(self, obj):
        if obj.image:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.image.url)
            return obj.image.url
        return None
    
    def get_subcategories(self, obj):
        # Filter only active subcategories and recursively serialize them
        active_subcategories = obj.subcategories.filter(is_active=True)
        if active_subcategories.exists():
            return CategorySerializer(active_subcategories, many=True, context=self.context).data
        return []


class ProductImageSerializer(serializers.ModelSerializer):
    image = serializers.SerializerMethodField()
    
    class Meta:
        model = ProductImage
        fields = ['id', 'image', 'alt_text', 'is_primary', 'created_at']
        read_only_fields = ['id', 'created_at']
    
    def get_image(self, obj):
        if obj.image:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.image.url)
            return obj.image.url
        return None


class ProductSerializer(serializers.ModelSerializer):
    store = StoreSerializer(read_only=True)
    category = CategorySerializer(read_only=True)
    images = ProductImageSerializer(many=True, read_only=True)
    average_rating = serializers.SerializerMethodField()
    review_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Product
        fields = ['id', 'name', 'description', 'store', 'category', 'price', 'discount_type', 'discount',
                 'stock_quantity', 'is_active', 'is_featured', 'is_approved', 'variants', 'images', 
                 'average_rating', 'review_count', 'item_code', 'created_at', 'updated_at']
        read_only_fields = ['id', 'item_code', 'created_at', 'updated_at']
        # Note: actual_price is excluded from customer-facing serializer
    
    def to_representation(self, instance):
        # Pass the request context to nested serializers
        data = super().to_representation(instance)
        request = self.context.get('request')
        
        # Update category with full image URL
        if data.get('category') and request:
            category_data = data['category']
            if category_data.get('image'):
                category_data['image'] = request.build_absolute_uri(category_data['image'])
        
        # Update images with full URLs
        if data.get('images') and request:
            for image_data in data['images']:
                if image_data.get('image'):
                    image_data['image'] = request.build_absolute_uri(image_data['image'])
        
        # Process variant combination images and remove actual_price from combinations
        if data.get('variants') and request:
            variants_data = data['variants']
            if isinstance(variants_data, dict) and variants_data.get('combinations'):
                combinations = variants_data['combinations']
                if isinstance(combinations, dict):
                    for combo_key, combo_data in combinations.items():
                        if isinstance(combo_data, dict):
                            # Remove actual_price from customer-facing response
                            if 'actual_price' in combo_data:
                                del combo_data['actual_price']
                            
                            # Process image URLs
                            if combo_data.get('image'):
                                image_path = combo_data['image']
                                # Only convert if it's a relative path (starts with /media/ or /)
                                # Skip local file paths (like /data/...) as they can't be accessed
                                if image_path and not image_path.startswith('http://') and not image_path.startswith('https://'):
                                    if image_path.startswith('/media/') or (image_path.startswith('/') and not image_path.startswith('/data/')):
                                        # Convert relative path to full URL
                                        try:
                                            combo_data['image'] = request.build_absolute_uri(image_path)
                                        except Exception:
                                            # If conversion fails, set to empty string
                                            combo_data['image'] = ''
                                    elif image_path.startswith('/data/'):
                                        # Local cache path - can't be accessed, set to empty
                                        combo_data['image'] = ''
        
        return data
    
    def get_average_rating(self, obj):
        reviews = obj.reviews.all()
        if reviews:
            return round(sum(review.rating for review in reviews) / len(reviews), 1)
        return 0
    
    def get_review_count(self, obj):
        return obj.reviews.count()


class ProductMerchantSerializer(serializers.ModelSerializer):
    store = StoreSerializer(read_only=True)
    category = CategorySerializer(read_only=True)
    images = ProductImageSerializer(many=True, read_only=True)
    average_rating = serializers.SerializerMethodField()
    review_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Product
        fields = ['id', 'name', 'description', 'store', 'category', 'actual_price', 'price', 
                 'discount_type', 'discount', 'stock_quantity', 'is_active', 'is_featured', 
                 'is_approved', 'variants', 'images', 'average_rating', 'review_count', 
                 'item_code', 'created_at', 'updated_at']
        read_only_fields = ['id', 'item_code', 'price', 'created_at', 'updated_at']
    
    def to_representation(self, instance):
        # Similar to ProductSerializer but keep actual_price in combinations
        data = super().to_representation(instance)
        request = self.context.get('request')
        
        # Update category with full image URL
        if data.get('category') and request:
            category_data = data['category']
            if category_data.get('image'):
                category_data['image'] = request.build_absolute_uri(category_data['image'])
        
        # Update images with full URLs
        if data.get('images') and request:
            for image_data in data['images']:
                if image_data.get('image'):
                    image_data['image'] = request.build_absolute_uri(image_data['image'])
        
        # Process variant combination images (keep actual_price, don't remove it)
        if data.get('variants') and request:
            variants_data = data['variants']
            if isinstance(variants_data, dict) and variants_data.get('combinations'):
                combinations = variants_data['combinations']
                if isinstance(combinations, dict):
                    for combo_key, combo_data in combinations.items():
                        if isinstance(combo_data, dict):
                            # Process image URLs (keep actual_price)
                            if combo_data.get('image'):
                                image_path = combo_data['image']
                                if image_path and not image_path.startswith('http://') and not image_path.startswith('https://'):
                                    if image_path.startswith('/media/') or (image_path.startswith('/') and not image_path.startswith('/data/')):
                                        try:
                                            combo_data['image'] = request.build_absolute_uri(image_path)
                                        except Exception:
                                            combo_data['image'] = ''
                                    elif image_path.startswith('/data/'):
                                        combo_data['image'] = ''
        
        return data
    
    def get_average_rating(self, obj):
        reviews = obj.reviews.all()
        if reviews:
            return round(sum(review.rating for review in reviews) / len(reviews), 1)
        return 0
    
    def get_review_count(self, obj):
        return obj.reviews.count()


class ProductCreateSerializer(serializers.ModelSerializer):
    # actual_price is what merchants input
    actual_price = serializers.DecimalField(max_digits=10, decimal_places=2, required=False, allow_null=True)
    # price is calculated from actual_price, so make it read-only
    price = serializers.DecimalField(max_digits=10, decimal_places=2, required=False, allow_null=True, read_only=True)
    stock_quantity = serializers.IntegerField(required=False, allow_null=True)
    # is_approved is read-only - only admins can set this
    is_approved = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = Product
        fields = ['name', 'description', 'store', 'category', 'actual_price', 'price', 'discount_type', 'discount',
                 'stock_quantity', 'is_active', 'is_featured', 'is_approved', 'variants', 'item_code']
        read_only_fields = ['item_code', 'price']
    
    def validate(self, data):
        """
        Validate product data, handling variant-enabled products.
        When variants are enabled, actual_price and stock_quantity are optional
        as they will be calculated from variant combinations in the model's save() method.
        """
        variants = data.get('variants', {})
        variants_enabled = isinstance(variants, dict) and variants.get('enabled', False)
        
        # If variants are enabled, validate combinations have actual_price
        if variants_enabled:
            combinations = variants.get('combinations', {})
            if isinstance(combinations, dict):
                for combo_key, combo_data in combinations.items():
                    if isinstance(combo_data, dict):
                        # actual_price should be provided for each combination
                        if 'actual_price' not in combo_data or not combo_data.get('actual_price'):
                            raise serializers.ValidationError({
                                'variants': f'Variant combination "{combo_key}" must have actual_price.'
                            })
            
            # Set defaults for product-level fields when variants enabled
            if 'stock_quantity' not in data or data.get('stock_quantity') is None:
                data['stock_quantity'] = 0  # Default, will be calculated from variant combinations
        else:
            # When variants are not enabled, actual_price is required
            if 'actual_price' not in data or data.get('actual_price') is None:
                raise serializers.ValidationError({
                    'actual_price': 'Actual price is required when variants are not enabled.'
                })
            if 'stock_quantity' not in data or data.get('stock_quantity') is None:
                raise serializers.ValidationError({
                    'stock_quantity': 'Stock quantity is required when variants are not enabled.'
                })
        
        return data


class CartSerializer(serializers.ModelSerializer):
    product = ProductSerializer(read_only=True)
    product_id = serializers.IntegerField(write_only=True)
    
    class Meta:
        model = Cart
        fields = ['id', 'product', 'product_id', 'quantity', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']


class OrderItemSerializer(serializers.ModelSerializer):
    product = ProductSerializer(read_only=True)
    store = StoreSerializer(read_only=True)
    
    class Meta:
        model = OrderItem
        fields = ['id', 'product', 'store', 'quantity', 'price', 'total', 'product_variant']
        read_only_fields = ['id', 'total']


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    user = UserSerializer(read_only=True)
    merchant = StoreSerializer(read_only=True)
    shipping_address = AddressSerializer(read_only=True)
    billing_address = AddressSerializer(read_only=True)
    
    class Meta:
        model = Order
        fields = ['id', 'order_number', 'user', 'merchant', 'status', 'subtotal', 'shipping_cost',
                 'total_amount', 'shipping_address', 'billing_address', 'phone', 'email', 'notes',
                 'items', 'payment_method', 'payment_status', 'merchant_ready_date', 'pickup_date',
                 'delivered_date', 'reject_reason',
                 'shipdaak_awb_number', 'shipdaak_shipment_id', 'shipdaak_order_id', 'shipdaak_label_url',
                 'shipdaak_manifest_url', 'shipdaak_status', 'shipdaak_courier_id', 'shipdaak_courier_name',
                 'package_length', 'package_breadth', 'package_height', 'package_weight',
                 'created_at', 'updated_at']
        read_only_fields = ['id', 'order_number', 'payment_status', 'merchant_ready_date', 'pickup_date',
                           'delivered_date',
                           'shipdaak_awb_number', 'shipdaak_shipment_id', 'shipdaak_order_id', 
                           'shipdaak_label_url', 'shipdaak_manifest_url', 'shipdaak_status',
                           'shipdaak_courier_id', 'shipdaak_courier_name', 'package_length', 
                           'package_breadth', 'package_height', 'package_weight', 'created_at', 'updated_at']


class OrderCreateSerializer(serializers.ModelSerializer):
    items = serializers.ListField(
        child=serializers.DictField(),
        write_only=True
    )
    shipping_address = serializers.IntegerField(required=True, help_text='Address ID for shipping address')
    billing_address = serializers.IntegerField(required=True, help_text='Address ID for billing address')
    
    class Meta:
        model = Order
        fields = ['shipping_address', 'billing_address', 'phone', 'email', 'notes', 'items', 'payment_method']
    
    def validate_shipping_address(self, value):
        """Validate that shipping address exists and belongs to the user"""
        from core.models import Address
        request = self.context.get('request')
        if request and request.user:
            try:
                address = Address.objects.get(id=value, user=request.user)
                return value
            except Address.DoesNotExist:
                raise serializers.ValidationError("Shipping address not found or does not belong to you.")
        return value
    
    def validate_billing_address(self, value):
        """Validate that billing address exists and belongs to the user"""
        from core.models import Address
        request = self.context.get('request')
        if request and request.user:
            try:
                address = Address.objects.get(id=value, user=request.user)
                return value
            except Address.DoesNotExist:
                raise serializers.ValidationError("Billing address not found or does not belong to you.")
        return value
    
    def create(self, validated_data):
        items_data = validated_data.pop('items')
        shipping_address_id = validated_data.pop('shipping_address')
        billing_address_id = validated_data.pop('billing_address')
        
        # Get address objects
        from core.models import Address, SuperSetting
        from .models import OrderItem, Store, Order, ShippingChargeHistory
        from collections import defaultdict
        from decimal import Decimal
        import random
        import string
        
        shipping_address = Address.objects.get(id=shipping_address_id)
        billing_address = Address.objects.get(id=billing_address_id)
        user = self.context['request'].user
        
        # Group items by vendor (store)
        vendor_items = defaultdict(list)
        for item_data in items_data:
            store_id = item_data.get('store')
            if store_id:
                try:
                    store = Store.objects.get(id=store_id)
                    vendor_items[store].append(item_data)
                except Store.DoesNotExist:
                    continue
        
        # Validate minimum order value for each merchant
        for store, vendor_items_list in vendor_items.items():
            vendor_subtotal = Decimal(str(sum(item.get('total', 0) for item in vendor_items_list)))
            minimum_order_value = Decimal(str(store.minimum_order_value))
            if minimum_order_value > 0 and vendor_subtotal < minimum_order_value:
                remaining = minimum_order_value - vendor_subtotal
                raise serializers.ValidationError(
                    f"Order value for {store.name} is {vendor_subtotal}, but minimum order value is {minimum_order_value}. Please add items worth {remaining} more."
                )
        
        # Create separate order for each vendor
        created_orders = []
        for store, vendor_items_list in vendor_items.items():
            # Calculate subtotal for this vendor (convert to Decimal)
            vendor_subtotal = Decimal(str(sum(item.get('total', 0) for item in vendor_items_list)))
            
            # Shipping is FREE for customers
            shipping_cost = Decimal('0')
            vendor_total = vendor_subtotal  # Total = subtotal (no shipping added)
            
            # Generate unique order number
            order_number = ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))
            while Order.objects.filter(order_number=order_number).exists():
                order_number = ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))
            
            # Create order for this vendor
            order_data = validated_data.copy()
            order_data.update({
                'merchant': store,
                'order_number': order_number,
                'subtotal': vendor_subtotal,
                'shipping_cost': shipping_cost,
                'total_amount': vendor_total,
                'shipping_address': shipping_address,
                'billing_address': billing_address,
            })
            
            order = Order.objects.create(**order_data)
            
            # Create order items for this vendor
            for item_data in vendor_items_list:
                # Get product to extract actual_price
                product = Product.objects.get(id=item_data['product'])
                actual_price_value = None
                
                # Extract actual_price based on variant or product
                if item_data.get('product_variant'):
                    # Has variant - extract from variant combination
                    variant_key = item_data['product_variant']  # Format: "Size:Small,Color:Red"
                    if product.variants and product.variants.get('enabled'):
                        combinations = product.variants.get('combinations', {})
                        # Convert variant key to combination key format (e.g., "Small/Red")
                        variant_parts = [part.split(':')[1] if ':' in part else part for part in variant_key.split(',')]
                        combo_key = '/'.join(variant_parts)
                        combination = combinations.get(combo_key, {})
                        if isinstance(combination, dict) and 'actual_price' in combination:
                            actual_price_value = Decimal(str(combination['actual_price']))
                else:
                    # No variant - use product.actual_price
                    if product.actual_price:
                        actual_price_value = Decimal(str(product.actual_price))
                
                # Fallback: if actual_price not found, use price (backward compatibility)
                if actual_price_value is None:
                    actual_price_value = Decimal(str(item_data.get('price', 0)))
                
                OrderItem.objects.create(
                    order=order,
                    product_id=item_data['product'],
                    store=store,
                    quantity=item_data['quantity'],
                    price=Decimal(str(item_data.get('price', 0))),
                    actual_price=actual_price_value,
                    total=Decimal(str(item_data.get('total', 0))),
                    product_variant=item_data.get('product_variant', '') or None
                )
            
            # Shipping charge history will be created when merchant accepts order
            
            # Send push notification to merchant
            try:
                from core.services.fcm_service import FCMService
                if store.owner:
                    FCMService.send_order_notification(store.owner, order)
            except Exception as e:
                import sys
                print(f"[ERROR] Failed to send order notification: {str(e)}")
                sys.stdout.flush()
            
            created_orders.append(order)
        
        # Store created orders in serializer instance for view to access
        self.created_orders = created_orders
        
        # Return the first order (for backward compatibility)
        # The view will handle returning all orders
        return created_orders[0] if created_orders else None


class ReviewSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    product = ProductSerializer(read_only=True)
    
    class Meta:
        model = Review
        fields = ['id', 'user', 'product', 'rating', 'title', 'comment', 
                 'is_verified_purchase', 'created_at', 'updated_at']
        read_only_fields = ['id', 'user', 'is_verified_purchase', 'created_at', 'updated_at']


class WishlistSerializer(serializers.ModelSerializer):
    product = ProductSerializer(read_only=True)
    product_id = serializers.IntegerField(write_only=True)
    
    class Meta:
        model = Wishlist
        fields = ['id', 'product', 'product_id', 'created_at']
        read_only_fields = ['id', 'created_at']


class CouponSerializer(serializers.ModelSerializer):
    is_valid = serializers.SerializerMethodField()
    
    class Meta:
        model = Coupon
        fields = ['id', 'code', 'description', 'discount_type', 'discount_value',
                 'minimum_amount', 'usage_limit', 'used_count', 'is_active',
                 'valid_from', 'valid_until', 'is_valid', 'created_at']
        read_only_fields = ['id', 'used_count', 'created_at']
    
    def get_is_valid(self, obj):
        return obj.is_valid()


class TransactionSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    transaction_type_display = serializers.CharField(source='get_transaction_type_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    related_order_number = serializers.CharField(source='related_order.order_number', read_only=True, allow_null=True)
    
    class Meta:
        model = Transaction
        fields = ['id', 'user', 'transaction_type', 'transaction_type_display', 'amount', 
                 'status', 'status_display', 'description', 'related_order', 'related_order_number',
                 'related_withdrawal', 'merchant_order_id', 'utr', 'bank_id', 'vpa', 'payer_name', 
                 'wallet_before', 'wallet_after', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']


class RevenueHistorySerializer(serializers.Serializer):
    """Serializer for revenue history entries"""
    order = OrderSerializer(read_only=True, allow_null=True)
    order_id = serializers.IntegerField()
    order_number = serializers.CharField()
    created_at = serializers.DateTimeField()
    order_status = serializers.CharField()
    payment_status = serializers.CharField()
    order_total = serializers.DecimalField(max_digits=10, decimal_places=2, coerce_to_string=False)
    shipping_cost = serializers.DecimalField(max_digits=10, decimal_places=2, coerce_to_string=False)
    commission = serializers.DecimalField(max_digits=10, decimal_places=2, coerce_to_string=False)
    revenue = serializers.DecimalField(max_digits=10, decimal_places=2, coerce_to_string=False)
    status = serializers.CharField()  # 'pending' or 'success'
    
    def to_representation(self, instance):
        """Convert dict to serializer representation"""
        if isinstance(instance, dict):
            # If instance is a dict, convert order to serializer
            data = instance.copy()
            if 'order' in data and data['order']:
                data['order'] = OrderSerializer(data['order'], context=self.context).data
            # Convert Decimal to float for JSON serialization
            for key in ['order_total', 'shipping_cost', 'commission', 'revenue']:
                if key in data:
                    value = data[key]
                    if isinstance(value, Decimal):
                        data[key] = float(value)
                    elif hasattr(value, '__float__'):
                        data[key] = float(value)
            return data
        return super().to_representation(instance)


class WithdrawalSerializer(serializers.ModelSerializer):
    merchant = UserSerializer(read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    payment_setting = serializers.SerializerMethodField()
    payment_details = serializers.SerializerMethodField()
    
    class Meta:
        model = Withdrawal
        fields = ['id', 'merchant', 'amount', 'status', 'status_display', 
                 'payment_setting', 'payment_details', 'rejection_reason', 
                 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_payment_setting(self, obj):
        """Get payment setting details"""
        if obj.payment_setting:
            # Return basic payment setting info to avoid circular import
            return {
                'id': obj.payment_setting.id,
                'payment_method_type': obj.payment_setting.payment_method_type,
                'payment_method_type_display': obj.payment_setting.get_payment_method_type_display(),
                'status': obj.payment_setting.status,
                'status_display': obj.payment_setting.get_status_display(),
            }
        return None
    
    def get_payment_details(self, obj):
        """Get payment details from payment_setting"""
        if obj.payment_setting and obj.payment_setting.payment_details:
            return obj.payment_setting.payment_details
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


class MerchantPaymentSettingSerializer(serializers.ModelSerializer):
    """Serializer for reading merchant payment settings"""
    user = UserSerializer(read_only=True)
    payment_method_type_display = serializers.CharField(source='get_payment_method_type_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    can_edit = serializers.SerializerMethodField()
    
    class Meta:
        model = MerchantPaymentSetting
        fields = ['id', 'user', 'payment_method_type', 'payment_method_type_display', 
                 'status', 'status_display', 'rejection_reason', 'payment_details',
                 'approved_at', 'rejected_at', 'can_edit', 'created_at', 'updated_at']
        read_only_fields = ['id', 'user', 'approved_at', 'rejected_at', 'created_at', 'updated_at']
    
    def get_can_edit(self, obj):
        """Return whether the payment setting can be edited"""
        return obj.can_edit()


class MerchantPaymentSettingCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating merchant payment settings"""
    
    class Meta:
        model = MerchantPaymentSetting
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
            # Optional: upi_id
            if 'upi_id' not in value:
                value['upi_id'] = value.get('vpa', '')
        
        elif payment_method_type == 'wallet':
            required_fields = ['wallet_type', 'wallet_id']
            for field in required_fields:
                if field not in value or not value[field]:
                    raise serializers.ValidationError(f"{field.replace('_', ' ').title()} is required for wallet")
            # Optional: wallet_provider
            if 'wallet_provider' not in value:
                value['wallet_provider'] = value.get('wallet_type', '')
        
        return value
    
    def create(self, validated_data):
        """Create payment setting for the authenticated merchant user"""
        user = self.context['request'].user
        if not user.is_merchant:
            raise serializers.ValidationError("Only merchants can create payment settings")
        
        # Check if payment setting already exists
        if MerchantPaymentSetting.objects.filter(user=user).exists():
            raise serializers.ValidationError("Payment setting already exists. Please update the existing one.")
        
        validated_data['user'] = user
        return super().create(validated_data)


class MerchantPaymentSettingUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating merchant payment settings (only if pending or rejected)"""
    
    class Meta:
        model = MerchantPaymentSetting
        fields = ['payment_method_type', 'payment_details']
    
    def validate(self, attrs):
        """Validate that payment setting can be edited"""
        instance = self.instance
        if instance and not instance.can_edit():
            raise serializers.ValidationError("Cannot edit payment setting that is already approved")
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
        """Update payment setting and reset status to pending if it was rejected"""
        if instance.status == 'rejected':
            # Reset to pending when updating a rejected payment setting
            validated_data['status'] = 'pending'
            validated_data['rejection_reason'] = None
            validated_data['rejected_at'] = None
        
        return super().update(instance, validated_data)


class BannerSerializer(serializers.ModelSerializer):
    image = serializers.SerializerMethodField()
    product_id = serializers.IntegerField(source='product.id', read_only=True, allow_null=True)
    
    class Meta:
        model = Banner
        fields = ['id', 'image', 'title', 'url', 'product_id', 'is_active', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_image(self, obj):
        if obj.image:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.image.url)
            return obj.image.url
        return None


class PopupSerializer(serializers.ModelSerializer):
    image = serializers.SerializerMethodField()
    product_id = serializers.IntegerField(source='product.id', read_only=True, allow_null=True)
    
    class Meta:
        model = Popup
        fields = ['id', 'image', 'title', 'url', 'product_id', 'is_active', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_image(self, obj):
        if obj.image:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.image.url)
            return obj.image.url
        return None


class ShippingChargeHistorySerializer(serializers.ModelSerializer):
    order = OrderSerializer(read_only=True)
    merchant = StoreSerializer(read_only=True)
    customer = UserSerializer(read_only=True)
    paid_by_display = serializers.CharField(source='get_paid_by_display', read_only=True)
    
    class Meta:
        model = ShippingChargeHistory
        fields = ['id', 'order', 'merchant', 'customer', 'shipping_charge', 
                 'courier_rate', 'commission', 'paid_by', 'paid_by_display', 'created_at']
        read_only_fields = ['id', 'created_at']

