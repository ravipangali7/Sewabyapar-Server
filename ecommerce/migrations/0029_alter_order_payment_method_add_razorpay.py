# Generated manually for Razorpay payment method

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ecommerce', '0028_store_is_opened'),
    ]

    operations = [
        migrations.AlterField(
            model_name='order',
            name='payment_method',
            field=models.CharField(choices=[('cod', 'Cash on Delivery'), ('online', 'Online Payment'), ('phonepe', 'PhonePe Payment'), ('razorpay', 'Razorpay Payment')], default='cod', max_length=10),
        ),
    ]
