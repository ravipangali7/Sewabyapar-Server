# Generated migration to remove basic_shipping_charge field

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0023_transaction_add_razorpay_payment'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='supersetting',
            name='basic_shipping_charge',
        ),
    ]
