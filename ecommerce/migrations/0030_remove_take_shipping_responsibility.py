# Generated migration to remove take_shipping_responsibility field

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('ecommerce', '0029_alter_order_payment_method_add_razorpay'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='store',
            name='take_shipping_responsibility',
        ),
    ]
