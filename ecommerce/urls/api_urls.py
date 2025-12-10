from django.urls import path
from ..views.api import (
    store_views, category_views, product_views,
    cart_views, order_views, review_views, wishlist_views, coupon_views, payment_views,
    merchant_views
)

urlpatterns = [
    # Store URLs
    path('stores/', store_views.store_list_create, name='store-list-create'),
    path('stores/<int:pk>/', store_views.store_detail, name='store-detail'),
    
    # Category URLs
    path('categories/', category_views.category_list_create, name='category-list-create'),
    path('categories/<int:pk>/', category_views.category_detail, name='category-detail'),
    
    # Product URLs
    path('products/', product_views.product_list_create, name='product-list-create'),
    path('products/<int:pk>/', product_views.product_detail, name='product-detail'),
    path('products/search/', product_views.search_products, name='product-search'),
    
    # Cart URLs
    path('cart/', cart_views.cart_list_create, name='cart-list-create'),
    path('cart/<int:pk>/', cart_views.cart_detail, name='cart-detail'),
    path('cart/add/', cart_views.add_to_cart, name='add-to-cart'),
    
    # Order URLs
    path('orders/', order_views.order_list_create, name='order-list-create'),
    path('orders/<int:pk>/', order_views.order_detail, name='order-detail'),
    path('orders/<int:pk>/cancel/', order_views.cancel_order, name='cancel-order'),
    
    # Review URLs
    path('reviews/', review_views.review_list_create, name='review-list-create'),
    path('reviews/<int:pk>/', review_views.review_detail, name='review-detail'),
    path('products/<int:product_id>/reviews/', review_views.review_list_create, name='product-reviews'),
    
    # Wishlist URLs
    path('wishlist/', wishlist_views.wishlist_list_create, name='wishlist-list-create'),
    path('wishlist/<int:pk>/', wishlist_views.wishlist_detail, name='wishlist-detail'),
    path('wishlist/add/', wishlist_views.add_to_wishlist, name='add-to-wishlist'),
    
    # Coupon URLs
    path('coupons/', coupon_views.coupon_list, name='coupon-list'),
    path('coupons/<str:code>/', coupon_views.coupon_detail, name='coupon-detail'),
    
    # Payment URLs
    path('payments/initiate/<int:order_id>/', payment_views.initiate_payment_view, name='initiate-payment'),
    path('payments/status/', payment_views.payment_status, name='payment-status'),
    path('payments/callback/', payment_views.payment_callback, name='payment-callback'),
    
    # Merchant URLs
    path('merchant/products/', merchant_views.merchant_products, name='merchant-products'),
    path('merchant/products/<int:pk>/', merchant_views.merchant_product_detail, name='merchant-product-detail'),
    path('merchant/orders/', merchant_views.merchant_orders, name='merchant-orders'),
    path('merchant/orders/<int:pk>/', merchant_views.merchant_order_detail, name='merchant-order-detail'),
    path('merchant/orders/<int:pk>/update-status/', merchant_views.merchant_order_update_status, name='merchant-order-update-status'),
    path('merchant/stats/', merchant_views.merchant_stats, name='merchant-stats'),
    path('merchant/stores/', merchant_views.merchant_stores, name='merchant-stores'),
    path('merchant/stores/<int:pk>/', merchant_views.merchant_store_detail, name='merchant-store-detail'),
]

