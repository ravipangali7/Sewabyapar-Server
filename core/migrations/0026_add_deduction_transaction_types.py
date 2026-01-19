# Generated manually

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0025_transaction_wallet_tracking'),
    ]

    operations = [
        migrations.AlterField(
            model_name='transaction',
            name='amount',
            field=models.DecimalField(decimal_places=2, help_text='Transaction amount (can be negative for deductions)', max_digits=10),
        ),
        migrations.AlterField(
            model_name='transaction',
            name='transaction_type',
            field=models.CharField(choices=[('commission', 'Commission'), ('commission_deduction', 'Commission Deduction'), ('shipping_charge_deduction', 'Shipping Charge Deduction'), ('withdrawal', 'Withdrawal Request'), ('withdrawal_processed', 'Withdrawal Processed'), ('phonepe_payment', 'PhonePe Payment'), ('sabpaisa_payment', 'SabPaisa Payment'), ('razorpay_payment', 'Razorpay Payment'), ('payout', 'Merchant Payout')], max_length=30),
        ),
    ]
