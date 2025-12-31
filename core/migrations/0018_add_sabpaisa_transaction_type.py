# Generated migration to add sabpaisa_payment transaction type

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0017_transaction_payer_name'),
    ]

    operations = [
        migrations.AlterField(
            model_name='transaction',
            name='transaction_type',
            field=models.CharField(
                choices=[
                    ('commission', 'Commission'),
                    ('withdrawal', 'Withdrawal Request'),
                    ('withdrawal_processed', 'Withdrawal Processed'),
                    ('phonepe_payment', 'PhonePe Payment'),
                    ('sabpaisa_payment', 'SabPaisa Payment'),
                    ('payout', 'Merchant Payout'),
                ],
                max_length=30
            ),
        ),
        migrations.AlterField(
            model_name='transaction',
            name='related_order',
            field=models.ForeignKey(
                blank=True,
                help_text='Related order for commission/payout/phonepe/sabpaisa transactions',
                null=True,
                on_delete=models.SET_NULL,
                related_name='transactions',
                to='ecommerce.order'
            ),
        ),
    ]
