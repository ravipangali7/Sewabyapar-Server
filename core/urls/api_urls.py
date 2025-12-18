from django.urls import path
from ..views.api import auth_views, setting_views, kyc_views
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
]
