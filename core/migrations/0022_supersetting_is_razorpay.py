# Generated manually for Razorpay payment method

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0021_supersetting_shipping_charge_commission'),
    ]

    operations = [
        migrations.AddField(
            model_name='supersetting',
            name='is_razorpay',
            field=models.BooleanField(default=True, help_text='Enable Razorpay payment method'),
        ),
    ]
