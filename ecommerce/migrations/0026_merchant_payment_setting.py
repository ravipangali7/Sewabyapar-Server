# Generated manually for Merchant Payment Setting

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ecommerce', '0025_add_store_shipping_fields_and_shipping_history'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='MerchantPaymentSetting',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('payment_method_type', models.CharField(choices=[('bank_account', 'Bank Account'), ('upi', 'UPI'), ('wallet', 'Wallet')], help_text='Type of payment method', max_length=20)),
                ('status', models.CharField(choices=[('pending', 'Pending'), ('approved', 'Approved'), ('rejected', 'Rejected')], default='pending', help_text='Verification status', max_length=20)),
                ('rejection_reason', models.TextField(blank=True, help_text='Reason for rejection if status is rejected', null=True)),
                ('payment_details', models.JSONField(default=dict, help_text='Payment method details (varies by payment_method_type)')),
                ('approved_at', models.DateTimeField(blank=True, help_text='When payment setting was approved', null=True)),
                ('rejected_at', models.DateTimeField(blank=True, help_text='When payment setting was rejected', null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('user', models.OneToOneField(limit_choices_to={'is_merchant': True}, on_delete=django.db.models.deletion.CASCADE, related_name='payment_setting', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Merchant Payment Setting',
                'verbose_name_plural': 'Merchant Payment Settings',
                'ordering': ['-created_at'],
            },
        ),
        migrations.AddIndex(
            model_name='merchantpaymentsetting',
            index=models.Index(fields=['user'], name='ecommerce_m_user_id_idx'),
        ),
        migrations.AddIndex(
            model_name='merchantpaymentsetting',
            index=models.Index(fields=['status', '-created_at'], name='ecommerce_m_status_c_idx'),
        ),
        migrations.AddField(
            model_name='withdrawal',
            name='payment_setting',
            field=models.ForeignKey(blank=True, help_text='Payment setting used for this withdrawal', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='withdrawals', to='ecommerce.merchantpaymentsetting'),
        ),
    ]
