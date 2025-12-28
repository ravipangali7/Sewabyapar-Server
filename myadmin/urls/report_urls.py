"""
Report URLs for admin panel
"""
from django.urls import path
from myadmin.views import report_views

app_name = 'reports'

urlpatterns = [
    path('finance/', report_views.FinanceReportView.as_view(), name='finance_report'),
    path('merchant/', report_views.MerchantReportView.as_view(), name='merchant_report'),
    path('customer/', report_views.CustomerReportView.as_view(), name='customer_report'),
]

