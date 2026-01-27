"""Core app URLs"""
from django.urls import path
from myadmin.views.core import user_views, address_views, otp_views, notification_views, kyc_views, supersetting_views, transaction_views, payment_method_views, withdrawal_views, agent_views

app_name = 'core'

urlpatterns = [
    # User URLs
    path('users/', user_views.UserListView.as_view(), name='user_list'),
    path('users/<int:pk>/', user_views.UserDetailView.as_view(), name='user_detail'),
    path('users/create/', user_views.UserCreateView.as_view(), name='user_create'),
    path('users/<int:pk>/update/', user_views.UserUpdateView.as_view(), name='user_update'),
    path('users/<int:pk>/delete/', user_views.UserDeleteView.as_view(), name='user_delete'),
    path('users/<int:pk>/verify-kyc/', user_views.verify_kyc, name='user_verify_kyc'),
    path('users/<int:pk>/toggle-edit-access/', user_views.toggle_edit_access, name='user_toggle_edit_access'),
    path('users/bulk-delete/', user_views.UserBulkDeleteView.as_view(), name='user_bulk_delete'),
    
    # KYC URLs
    path('kyc/', kyc_views.KYCListView.as_view(), name='kyc_list'),
    path('kyc/<int:user_id>/', kyc_views.KYCVerificationView.as_view(), name='kyc_verification'),
    path('kyc/<int:user_id>/verify/', kyc_views.KYCVerifyView.as_view(), name='kyc_verify'),
    path('kyc/<int:user_id>/reject/', kyc_views.KYCRejectView.as_view(), name='kyc_reject'),
    path('kyc/bulk-verify/', kyc_views.KYCBulkVerifyView.as_view(), name='kyc_bulk_verify'),
    
    # Merchant KYC URLs
    path('merchant-kyc/pending/', kyc_views.MerchantKYCPendingView.as_view(), name='merchant_kyc_pending'),
    path('merchant-kyc/verified/', kyc_views.MerchantKYCVerifiedView.as_view(), name='merchant_kyc_verified'),
    path('merchant-kyc/rejected/', kyc_views.MerchantKYCRejectedView.as_view(), name='merchant_kyc_rejected'),
    
    # Customer KYC URLs
    path('customer-kyc/pending/', kyc_views.CustomerKYCPendingView.as_view(), name='customer_kyc_pending'),
    path('customer-kyc/verified/', kyc_views.CustomerKYCVerifiedView.as_view(), name='customer_kyc_verified'),
    path('customer-kyc/rejected/', kyc_views.CustomerKYCRejectedView.as_view(), name='customer_kyc_rejected'),
    
    # Address URLs
    path('addresses/', address_views.AddressListView.as_view(), name='address_list'),
    path('addresses/<int:pk>/', address_views.AddressDetailView.as_view(), name='address_detail'),
    path('addresses/create/', address_views.AddressCreateView.as_view(), name='address_create'),
    path('addresses/<int:pk>/update/', address_views.AddressUpdateView.as_view(), name='address_update'),
    path('addresses/<int:pk>/delete/', address_views.AddressDeleteView.as_view(), name='address_delete'),
    
    # OTP URLs (read-only)
    path('otps/', otp_views.OtpListView.as_view(), name='otp_list'),
    path('otps/<int:pk>/', otp_views.OtpDetailView.as_view(), name='otp_detail'),
    
    # Notification URLs
    path('notifications/', notification_views.NotificationListView.as_view(), name='notification_list'),
    path('notifications/<int:pk>/', notification_views.NotificationDetailView.as_view(), name='notification_detail'),
    path('notifications/create/', notification_views.NotificationCreateView.as_view(), name='notification_create'),
    path('notifications/<int:pk>/update/', notification_views.NotificationUpdateView.as_view(), name='notification_update'),
    path('notifications/<int:pk>/delete/', notification_views.NotificationDeleteView.as_view(), name='notification_delete'),
    
    # SuperSetting URLs (singleton - update only)
    path('supersetting/', supersetting_views.SuperSettingDetailView.as_view(), name='supersetting_detail'),
    path('supersetting/update/', supersetting_views.SuperSettingUpdateView.as_view(), name='supersetting_update'),
    
    # Transaction URLs
    path('transactions/', transaction_views.TransactionListView.as_view(), name='transaction_list'),
    path('transactions/<int:pk>/', transaction_views.TransactionDetailView.as_view(), name='transaction_detail'),
    path('transactions/create/', transaction_views.TransactionCreateView.as_view(), name='transaction_create'),
    path('transactions/<int:pk>/update/', transaction_views.TransactionUpdateView.as_view(), name='transaction_update'),
    path('transactions/<int:pk>/delete/', transaction_views.TransactionDeleteView.as_view(), name='transaction_delete'),
    
    # User Payment Method URLs
    path('payment-methods/', payment_method_views.PaymentMethodListView.as_view(), name='payment_method_list'),
    path('payment-methods/create/', payment_method_views.PaymentMethodCreateView.as_view(), name='payment_method_create'),
    path('payment-methods/<int:pk>/', payment_method_views.PaymentMethodDetailView.as_view(), name='payment_method_detail'),
    path('payment-methods/<int:pk>/update/', payment_method_views.PaymentMethodUpdateView.as_view(), name='payment_method_update'),
    path('payment-methods/<int:pk>/delete/', payment_method_views.PaymentMethodDeleteView.as_view(), name='payment_method_delete'),
    path('payment-methods/<int:pk>/approve/', payment_method_views.PaymentMethodApproveView.as_view(), name='payment_method_approve'),
    path('payment-methods/<int:pk>/reject/', payment_method_views.PaymentMethodRejectView.as_view(), name='payment_method_reject'),
    path('payment-methods/bulk-approve/', payment_method_views.PaymentMethodBulkApproveView.as_view(), name='payment_method_bulk_approve'),
    
    # Withdrawal URLs
    path('withdrawals/', withdrawal_views.WithdrawalListView.as_view(), name='withdrawal_list'),
    path('withdrawals/<int:pk>/', withdrawal_views.WithdrawalDetailView.as_view(), name='withdrawal_detail'),
    path('withdrawals/create/', withdrawal_views.WithdrawalCreateView.as_view(), name='withdrawal_create'),
    path('withdrawals/<int:pk>/update/', withdrawal_views.WithdrawalUpdateView.as_view(), name='withdrawal_update'),
    path('withdrawals/<int:pk>/delete/', withdrawal_views.WithdrawalDeleteView.as_view(), name='withdrawal_delete'),
    path('withdrawals/<int:pk>/approve/', withdrawal_views.WithdrawalApproveView.as_view(), name='withdrawal_approve'),
    path('withdrawals/<int:pk>/reject/', withdrawal_views.WithdrawalRejectView.as_view(), name='withdrawal_reject'),
    
    # Agent URLs
    path('agents/', agent_views.AgentListView.as_view(), name='agent_list'),
    path('agents/<int:pk>/', agent_views.AgentDetailView.as_view(), name='agent_detail'),
    path('agents/create/', agent_views.AgentCreateView.as_view(), name='agent_create'),
    path('agents/<int:pk>/update/', agent_views.AgentUpdateView.as_view(), name='agent_update'),
    path('agents/<int:pk>/delete/', agent_views.AgentDeleteView.as_view(), name='agent_delete'),
]

