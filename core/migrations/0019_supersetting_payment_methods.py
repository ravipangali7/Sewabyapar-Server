# Generated manually for payment method settings

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0018_add_sabpaisa_payment_transaction_type'),
    ]

    operations = [
        migrations.AddField(
            model_name='supersetting',
            name='is_phone_pe',
            field=models.BooleanField(default=True, help_text='Enable PhonePe payment method'),
        ),
        migrations.AddField(
            model_name='supersetting',
            name='is_sabpaisa',
            field=models.BooleanField(default=True, help_text='Enable SabPaisa payment method'),
        ),
        migrations.AddField(
            model_name='supersetting',
            name='is_cod',
            field=models.BooleanField(default=True, help_text='Enable Cash on Delivery payment method'),
        ),
    ]
