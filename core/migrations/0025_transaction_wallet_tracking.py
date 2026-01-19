# Generated migration to add wallet tracking fields to Transaction

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0024_remove_basic_shipping_charge'),
    ]

    operations = [
        migrations.AddField(
            model_name='transaction',
            name='wallet_before',
            field=models.DecimalField(blank=True, decimal_places=2, help_text='Wallet balance before this transaction', max_digits=10, null=True),
        ),
        migrations.AddField(
            model_name='transaction',
            name='wallet_after',
            field=models.DecimalField(blank=True, decimal_places=2, help_text='Wallet balance after this transaction', max_digits=10, null=True),
        ),
    ]
