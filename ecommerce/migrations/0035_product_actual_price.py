# Generated manually for actual_price field

from django.db import migrations, models
import django.core.validators


class Migration(migrations.Migration):

    dependencies = [
        ('ecommerce', '0034_alter_withdrawal_status'),
    ]

    operations = [
        migrations.AddField(
            model_name='product',
            name='actual_price',
            field=models.DecimalField(blank=True, decimal_places=2, help_text='Merchant price before commission', max_digits=10, null=True, validators=[django.core.validators.MinValueValidator(0)]),
        ),
    ]
