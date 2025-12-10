from rest_framework import serializers
from .models import (
    Store, Category, Product, ProductImage, Cart, Order, OrderItem, 
    Review, Wishlist, Coupon
)
from core.serializers import UserSerializer


class StoreSerializer(serializers.ModelSerializer):
    owner = UserSerializer(read_only=True)
    
    class Meta:
        model = Store
        fields = ['id', 'name', 'description', 'owner', 'logo', 'banner', 'address', 
                 'phone', 'email', 'is_active', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def to_representation(self, instance):
        data = super().to_representation(instance)
        request = self.context.get('request')
        
        # Convert logo and banner to full URLs
        if data.get('logo') and request:
            data['logo'] = request.build_absolute_uri(instance.logo.url) if instance.logo else None
        if data.get('banner') and request:
            data['banner'] = request.build_absolute_uri(instance.banner.url) if instance.banner else None
        
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
        if obj.subcategories.exists():
            return CategorySerializer(obj.subcategories.all(), many=True, context=self.context).data
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
        fields = ['id', 'name', 'description', 'store', 'category', 'price', 'compare_price',
                 'sku', 'stock_quantity', 'is_active', 'is_featured', 'weight', 'dimensions',
                 'images', 'average_rating', 'review_count', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']
    
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
        
        return data
    
    def get_average_rating(self, obj):
        reviews = obj.reviews.all()
        if reviews:
            return round(sum(review.rating for review in reviews) / len(reviews), 1)
        return 0
    
    def get_review_count(self, obj):
        return obj.reviews.count()


class ProductCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = ['name', 'description', 'store', 'category', 'price', 'compare_price',
                 'sku', 'stock_quantity', 'is_active', 'is_featured', 'weight', 'dimensions']


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
        fields = ['id', 'product', 'store', 'quantity', 'price', 'total']
        read_only_fields = ['id', 'total']


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    user = UserSerializer(read_only=True)
    
    class Meta:
        model = Order
        fields = ['id', 'order_number', 'user', 'status', 'total_amount', 'shipping_address',
                 'billing_address', 'phone', 'email', 'notes', 'items', 'payment_method',
                 'payment_status', 'phonepe_transaction_id', 'phonepe_merchant_order_id',
                 'created_at', 'updated_at']
        read_only_fields = ['id', 'order_number', 'payment_status', 'phonepe_transaction_id',
                           'phonepe_merchant_order_id', 'created_at', 'updated_at']


class OrderCreateSerializer(serializers.ModelSerializer):
    items = serializers.ListField(
        child=serializers.DictField(),
        write_only=True
    )
    
    class Meta:
        model = Order
        fields = ['shipping_address', 'billing_address', 'phone', 'email', 'notes', 'items', 'payment_method']
    
    def create(self, validated_data):
        items_data = validated_data.pop('items')
        
        # Calculate total amount from items
        total_amount = sum(item.get('total', 0) for item in items_data)
        validated_data['total_amount'] = total_amount
        
        # Create the order
        order = super().create(validated_data)
        
        # Create order items
        from .models import OrderItem
        for item_data in items_data:
            OrderItem.objects.create(
                order=order,
                product_id=item_data['product'],
                store_id=item_data['store'],
                quantity=item_data['quantity'],
                price=item_data['price'],
                total=item_data['total']
            )
        
        return order


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

