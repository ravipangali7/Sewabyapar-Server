# Generated manually for actual_price field in OrderItem

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ecommerce', '0035_product_actual_price'),
    ]

    operations = [
        migrations.AddField(
            model_name='orderitem',
            name='actual_price',
            field=models.DecimalField(blank=True, decimal_places=2, help_text='Merchant price before commission at time of order', max_digits=10, null=True),
        ),
    ]
