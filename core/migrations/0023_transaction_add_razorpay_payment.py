# Generated manually for Razorpay payment transaction type

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0022_supersetting_is_razorpay'),
    ]

    operations = [
        migrations.AlterField(
            model_name='transaction',
            name='transaction_type',
            field=models.CharField(choices=[('commission', 'Commission'), ('withdrawal', 'Withdrawal Request'), ('withdrawal_processed', 'Withdrawal Processed'), ('phonepe_payment', 'PhonePe Payment'), ('sabpaisa_payment', 'SabPaisa Payment'), ('razorpay_payment', 'Razorpay Payment'), ('payout', 'Merchant Payout')], max_length=30),
        ),
    ]
