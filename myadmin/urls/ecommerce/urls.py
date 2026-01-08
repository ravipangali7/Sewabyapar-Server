"""Ecommerce app URLs"""
from django.urls import path
from myadmin.views.ecommerce import (
    product_views, category_views, store_views, order_views,
    review_views, cart_views, wishlist_views, coupon_views,
    product_image_views, order_item_views, banner_views, popup_views,
    shipping_charge_history_views, payment_setting_views
)

app_name = 'ecommerce'

urlpatterns = [
    # Product URLs
    path('products/', product_views.ProductListView.as_view(), name='product_list'),
    path('products/<int:pk>/', product_views.ProductDetailView.as_view(), name='product_detail'),
    path('products/create/', product_views.ProductCreateView.as_view(), name='product_create'),
    path('products/<int:pk>/update/', product_views.ProductUpdateView.as_view(), name='product_update'),
    path('products/<int:pk>/delete/', product_views.ProductDeleteView.as_view(), name='product_delete'),
    path('products/<int:pk>/approve/', product_views.ProductApproveView.as_view(), name='product_approve'),
    path('products/<int:pk>/reject/', product_views.ProductRejectView.as_view(), name='product_reject'),
    path('products/bulk-delete/', product_views.ProductBulkDeleteView.as_view(), name='product_bulk_delete'),
    path('products/bulk-activate/', product_views.ProductBulkActivateView.as_view(), name='product_bulk_activate'),
    path('products/bulk-deactivate/', product_views.ProductBulkDeactivateView.as_view(), name='product_bulk_deactivate'),
    
    # Category URLs
    path('categories/', category_views.CategoryListView.as_view(), name='category_list'),
    path('categories/<int:pk>/', category_views.CategoryDetailView.as_view(), name='category_detail'),
    path('categories/create/', category_views.CategoryCreateView.as_view(), name='category_create'),
    path('categories/<int:pk>/update/', category_views.CategoryUpdateView.as_view(), name='category_update'),
    path('categories/<int:pk>/delete/', category_views.CategoryDeleteView.as_view(), name='category_delete'),
    
    # Store URLs
    path('stores/', store_views.StoreListView.as_view(), name='store_list'),
    path('stores/<int:pk>/', store_views.StoreDetailView.as_view(), name='store_detail'),
    path('stores/create/', store_views.StoreCreateView.as_view(), name='store_create'),
    path('stores/<int:pk>/update/', store_views.StoreUpdateView.as_view(), name='store_update'),
    path('stores/<int:pk>/delete/', store_views.StoreDeleteView.as_view(), name='store_delete'),
    path('stores/<int:pk>/toggle-is-opened/', store_views.toggle_is_opened, name='store_toggle_is_opened'),
    
    # Order URLs
    path('orders/', order_views.OrderListView.as_view(), name='order_list'),
    path('orders/<int:pk>/', order_views.OrderDetailView.as_view(), name='order_detail'),
    path('orders/create/', order_views.OrderCreateView.as_view(), name='order_create'),
    path('orders/<int:pk>/update/', order_views.OrderUpdateView.as_view(), name='order_update'),
    path('orders/<int:pk>/delete/', order_views.OrderDeleteView.as_view(), name='order_delete'),
    path('orders/<int:pk>/cancel/', order_views.CancelOrderView.as_view(), name='order_cancel'),
    path('orders/<int:pk>/update-status/', order_views.update_order_status, name='order_update_status'),
    path('orders/bulk-delete/', order_views.OrderBulkDeleteView.as_view(), name='order_bulk_delete'),
    path('orders/bulk-status-update/', order_views.OrderBulkStatusUpdateView.as_view(), name='order_bulk_status_update'),
    
    # OrderItem URLs (read-only)
    path('order-items/', order_item_views.OrderItemListView.as_view(), name='order_item_list'),
    path('order-items/<int:pk>/', order_item_views.OrderItemDetailView.as_view(), name='order_item_detail'),
    
    # Shipping Charge History URLs (read-only)
    path('shipping-charge-history/', shipping_charge_history_views.ShippingChargeHistoryListView.as_view(), name='shipping_charge_history_list'),
    path('shipping-charge-history/<int:pk>/', shipping_charge_history_views.ShippingChargeHistoryDetailView.as_view(), name='shipping_charge_history_detail'),
    
    # Review URLs
    path('reviews/', review_views.ReviewListView.as_view(), name='review_list'),
    path('reviews/<int:pk>/', review_views.ReviewDetailView.as_view(), name='review_detail'),
    path('reviews/create/', review_views.ReviewCreateView.as_view(), name='review_create'),
    path('reviews/<int:pk>/update/', review_views.ReviewUpdateView.as_view(), name='review_update'),
    path('reviews/<int:pk>/delete/', review_views.ReviewDeleteView.as_view(), name='review_delete'),
    
    # Cart URLs
    path('carts/', cart_views.CartListView.as_view(), name='cart_list'),
    path('carts/<int:pk>/', cart_views.CartDetailView.as_view(), name='cart_detail'),
    path('carts/<int:pk>/delete/', cart_views.CartDeleteView.as_view(), name='cart_delete'),
    
    # Wishlist URLs
    path('wishlists/', wishlist_views.WishlistListView.as_view(), name='wishlist_list'),
    path('wishlists/<int:pk>/', wishlist_views.WishlistDetailView.as_view(), name='wishlist_detail'),
    path('wishlists/<int:pk>/delete/', wishlist_views.WishlistDeleteView.as_view(), name='wishlist_delete'),
    
    # Coupon URLs
    path('coupons/', coupon_views.CouponListView.as_view(), name='coupon_list'),
    path('coupons/<int:pk>/', coupon_views.CouponDetailView.as_view(), name='coupon_detail'),
    path('coupons/create/', coupon_views.CouponCreateView.as_view(), name='coupon_create'),
    path('coupons/<int:pk>/update/', coupon_views.CouponUpdateView.as_view(), name='coupon_update'),
    path('coupons/<int:pk>/delete/', coupon_views.CouponDeleteView.as_view(), name='coupon_delete'),
    
    # ProductImage URLs
    path('product-images/', product_image_views.ProductImageListView.as_view(), name='product_image_list'),
    path('product-images/create/', product_image_views.ProductImageCreateView.as_view(), name='product_image_create'),
    path('product-images/<int:pk>/update/', product_image_views.ProductImageUpdateView.as_view(), name='product_image_update'),
    path('product-images/<int:pk>/delete/', product_image_views.ProductImageDeleteView.as_view(), name='product_image_delete'),
    
    # Banner URLs
    path('banners/', banner_views.BannerListView.as_view(), name='banner_list'),
    path('banners/<int:pk>/', banner_views.BannerDetailView.as_view(), name='banner_detail'),
    path('banners/create/', banner_views.BannerCreateView.as_view(), name='banner_create'),
    path('banners/<int:pk>/update/', banner_views.BannerUpdateView.as_view(), name='banner_update'),
    path('banners/<int:pk>/delete/', banner_views.BannerDeleteView.as_view(), name='banner_delete'),
    
    # Popup URLs
    path('popups/', popup_views.PopupListView.as_view(), name='popup_list'),
    path('popups/<int:pk>/', popup_views.PopupDetailView.as_view(), name='popup_detail'),
    path('popups/create/', popup_views.PopupCreateView.as_view(), name='popup_create'),
    path('popups/<int:pk>/update/', popup_views.PopupUpdateView.as_view(), name='popup_update'),
    path('popups/<int:pk>/delete/', popup_views.PopupDeleteView.as_view(), name='popup_delete'),
    
    # Payment Setting URLs
    path('payment-settings/', payment_setting_views.PaymentSettingListView.as_view(), name='payment_setting_list'),
    path('payment-settings/<int:pk>/', payment_setting_views.PaymentSettingDetailView.as_view(), name='payment_setting_detail'),
    path('payment-settings/<int:pk>/approve/', payment_setting_views.PaymentSettingApproveView.as_view(), name='payment_setting_approve'),
    path('payment-settings/<int:pk>/reject/', payment_setting_views.PaymentSettingRejectView.as_view(), name='payment_setting_reject'),
    path('payment-settings/bulk-approve/', payment_setting_views.PaymentSettingBulkApproveView.as_view(), name='payment_setting_bulk_approve'),
]

