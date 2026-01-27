from django.urls import path
from ..views.api import auth_views, setting_views, kyc_views, cms_views, payment_method_views, withdrawal_views
from ..views import address_views, notification_views

urlpatterns = [
    # User/Auth URLs
    path('auth/register/', auth_views.user_register, name='user-register'),
    path('auth/register/send-otp/', auth_views.send_registration_otp, name='send-registration-otp'),
    path('auth/register/verify-otp/', auth_views.verify_otp_and_register, name='verify-otp-and-register'),
    path('auth/register/resend-otp/', auth_views.resend_otp, name='resend-otp'),
    path('auth/forgot-password/send-otp/', auth_views.send_forgot_password_otp, name='send-forgot-password-otp'),
    path('auth/forgot-password/verify-otp/', auth_views.verify_forgot_password_otp, name='verify-forgot-password-otp'),
    path('auth/forgot-password/reset-password/', auth_views.reset_password, name='reset-password'),
    path('auth/login/', auth_views.user_login, name='user-login'),
    path('auth/logout/', auth_views.user_logout, name='user-logout'),
    path('auth/delete-account/', auth_views.delete_account, name='delete-account'),
    path('auth/upgrade-account/', auth_views.upgrade_account, name='upgrade-account'),
    path('auth/switch-mode/', auth_views.switch_mode, name='switch-mode'),
    path('auth/profile/', auth_views.user_profile, name='user-profile'),
    path('auth/user/', auth_views.user_detail, name='user-detail'),
    
    # Address URLs
    path('addresses/', address_views.address_list_create, name='address-list-create'),
    path('addresses/<int:pk>/', address_views.address_detail, name='address-detail'),
    path('addresses/<int:pk>/set-default/', address_views.set_default_address, name='set-default-address'),
    
    # Notification URLs
    path('notifications/', notification_views.notification_list, name='notification-list'),
    path('notifications/<int:pk>/', notification_views.notification_detail, name='notification-detail'),
    path('notifications/<int:pk>/mark-read/', notification_views.mark_notification_read, name='mark-notification-read'),
    path('notifications/mark-all-read/', notification_views.mark_all_notifications_read, name='mark-all-notifications-read'),
    
    # SuperSetting URLs
    path('super-setting/', setting_views.super_setting, name='super-setting'),
    
    # KYC URLs
    path('kyc/submit/', kyc_views.kyc_submit, name='kyc-submit'),
    path('kyc/status/', kyc_views.kyc_status, name='kyc-status'),
    
    # CMS Pages URLs
    path('cms-pages/<slug:slug>/', cms_views.cms_page_by_slug, name='cms-page-by-slug'),
    
    # Contact Form URL
    path('contact/submit/', cms_views.contact_form_submit, name='contact-submit'),
    
    # Website Settings URL
    path('website-settings/', cms_views.website_settings, name='website-settings'),
    
    # Payment Method URLs
    path('merchant/payment-method/', payment_method_views.get_payment_method, name='get-payment-method'),
    path('merchant/payment-method/create/', payment_method_views.create_payment_method, name='create-payment-method'),
    path('merchant/payment-method/update/', payment_method_views.update_payment_method, name='update-payment-method'),
    path('merchant/payment-method/delete/', payment_method_views.delete_payment_method, name='delete-payment-method'),
    
    # Withdrawal URLs
    path('merchant/withdrawals/', withdrawal_views.withdrawal_list, name='withdrawal-list'),
    path('merchant/withdrawals/create/', withdrawal_views.create_withdrawal, name='create-withdrawal'),
    path('merchant/withdrawals/<int:pk>/', withdrawal_views.withdrawal_detail, name='withdrawal-detail'),
]
