from django.urls import path
from .views import views
from .views import ecommerce, taxi_view, auth, profile

app_name = 'website'

urlpatterns = [
    # General website routes
    path('', views.home_view, name='home'),
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('page/<slug:slug>/', views.cms_page_view, name='cms_page'),
    path('contact/', views.contact_form_view, name='contact_form'),
    
    # Ecommerce routes
    path('shop/', ecommerce.shop_view, name='shop'),
    path('products/', ecommerce.products_view, name='products'),
    path('products/<int:product_id>/', ecommerce.product_detail_view, name='product_detail'),
    path('categories/', ecommerce.categories_view, name='categories'),
    path('cart/', ecommerce.cart_view, name='cart'),
    path('checkout/', ecommerce.checkout_view, name='checkout'),
    path('checkout/process/', ecommerce.process_checkout, name='process_checkout'),
    path('orders/', ecommerce.orders_view, name='orders'),
    path('orders/<int:order_id>/', ecommerce.order_detail_view, name='order_detail'),
    path('wishlist/', ecommerce.wishlist_view, name='wishlist'),
    path('search/', ecommerce.search_view, name='search'),
    
    # Taxi routes
    path('taxi/', taxi_view.taxi_view, name='taxi'),
    path('taxi/new-booking/', taxi_view.new_booking_view, name='new_taxi_booking'),
    path('taxi/my-bookings/', taxi_view.my_bookings_view, name='my_taxi_bookings'),
    path('taxi/bookings/<int:booking_id>/', taxi_view.booking_detail_view, name='taxi_booking_detail'),
    
    # Auth routes
    path('login/', auth.login_view, name='login'),
    path('logout/', auth.logout_view, name='logout'),
    path('register/', auth.register_view, name='register'),
    path('forgot-password/', auth.forgot_password_view, name='forgot_password'),
    path('reset-password/', auth.reset_password_view, name='reset_password'),
    
    # Profile routes
    path('profile/', profile.profile_view, name='profile'),
    path('profile/edit/', profile.edit_profile_view, name='edit_profile'),
    path('profile/addresses/', profile.addresses_view, name='addresses'),
    path('profile/notifications/', profile.notifications_view, name='notifications'),
    path('profile/feedback/', profile.feedback_complain_view, name='feedback_complain'),
    path('profile/feedback/<int:feedback_id>/', profile.feedback_detail_view, name='feedback_detail'),
    path('profile/help-support/', profile.help_support_view, name='help_support'),
    path('profile/kyc/', profile.kyc_submit_view, name='kyc_submit'),
    path('profile/kyc/status/', profile.kyc_status_view, name='kyc_status'),
]
