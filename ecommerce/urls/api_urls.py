from django.urls import path
from ..views.api import (
    store_views, category_views, product_views,
    cart_views, order_views, review_views, wishlist_views, coupon_views, payment_views,
    merchant_views, transaction_views, banner_views, popup_views,
    shipping_charge_history_views
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
    path('orders/validate/', order_views.validate_cart_for_order, name='validate-cart-for-order'),
    path('orders/', order_views.order_list_create, name='order-list-create'),
    path('orders/create-after-razorpay/', order_views.create_order_after_razorpay_payment, name='create-order-after-razorpay'),
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
    path('payments/create-order-token/<int:order_id>/', payment_views.create_order_token_for_mobile, name='create-order-token-mobile'),
    path('payments/status/', payment_views.payment_status, name='payment-status'),
    path('payments/callback/', payment_views.payment_callback, name='payment-callback'),
    # SabPaisa Payment URLs
    path('payments/sabpaisa/initiate/<int:order_id>/', payment_views.initiate_sabpaisa_payment_view, name='initiate-sabpaisa-payment'),
    path('payments/sabpaisa/save-transaction/<int:order_id>/', payment_views.save_sabpaisa_transaction_view, name='save-sabpaisa-transaction'),
    path('payments/sabpaisa/callback/', payment_views.sabpaisa_payment_callback, name='sabpaisa-payment-callback'),
    # Razorpay Payment URLs
    path('payments/razorpay/status/', payment_views.razorpay_payment_status, name='razorpay-payment-status'),
    path('payments/razorpay/callback/', payment_views.razorpay_payment_callback, name='razorpay-payment-callback'),
    
    # Merchant URLs
    path('merchant/products/', merchant_views.merchant_products, name='merchant-products'),
    path('merchant/products/<int:pk>/', merchant_views.merchant_product_detail, name='merchant-product-detail'),
    path('merchant/orders/', merchant_views.merchant_orders, name='merchant-orders'),
    path('merchant/orders/<int:pk>/', merchant_views.merchant_order_detail, name='merchant-order-detail'),
    path('merchant/orders/<int:pk>/update-status/', merchant_views.merchant_order_update_status, name='merchant-order-update-status'),
    path('merchant/orders/<int:pk>/accept/', merchant_views.merchant_accept_order, name='merchant-accept-order'),
    path('merchant/orders/<int:pk>/reject/', merchant_views.merchant_reject_order, name='merchant-reject-order'),
    path('merchant/orders/<int:pk>/courier-rates/', merchant_views.merchant_get_courier_rates, name='merchant-get-courier-rates'),
    path('merchant/stats/', merchant_views.merchant_stats, name='merchant-stats'),
    path('merchant/revenue-history/', merchant_views.merchant_revenue_history, name='merchant-revenue-history'),
    path('merchant/stores/', merchant_views.merchant_stores, name='merchant-stores'),
    path('merchant/stores/<int:pk>/', merchant_views.merchant_store_detail, name='merchant-store-detail'),
    # Shipdaak shipment URLs
    path('merchant/shipments/track/<str:awb_number>/', merchant_views.merchant_shipments_track, name='merchant-shipments-track'),
    path('merchant/shipments/cancel/', merchant_views.merchant_shipments_cancel, name='merchant-shipments-cancel'),
    path('merchant/couriers/', merchant_views.merchant_couriers, name='merchant-couriers'),
    path('merchant/couriers/available/', merchant_views.merchant_get_available_couriers, name='merchant-get-available-couriers'),
    
    # Transaction URLs
    path('transactions/', transaction_views.transaction_list, name='transaction-list'),
    path('transactions/<int:pk>/', transaction_views.transaction_detail, name='transaction-detail'),
    path('merchant/transactions/', transaction_views.merchant_transactions, name='merchant-transactions'),
    path('merchant/wallet/', transaction_views.merchant_wallet, name='merchant-wallet'),
    
    # Shipping Charge History URLs
    path('shipping-charge-history/', shipping_charge_history_views.shipping_charge_history_list, name='shipping-charge-history-list'),
    path('shipping-charge-history/<int:pk>/', shipping_charge_history_views.shipping_charge_history_detail, name='shipping-charge-history-detail'),
    path('merchant/shipping-charge-history/', shipping_charge_history_views.merchant_shipping_charge_history_list, name='merchant-shipping-charge-history-list'),
    
    # Banner URLs
    path('banners/', banner_views.banner_list, name='banner-list'),
    
    # Popup URLs
    path('popups/', popup_views.popup_list, name='popup-list'),
]

