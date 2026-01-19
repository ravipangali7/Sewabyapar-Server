# Generated migration to add courier_rate and commission fields to ShippingChargeHistory

from django.db import migrations, models
import django.core.validators


class Migration(migrations.Migration):

    dependencies = [
        ('ecommerce', '0030_remove_take_shipping_responsibility'),
    ]

    operations = [
        migrations.AddField(
            model_name='shippingchargehistory',
            name='courier_rate',
            field=models.DecimalField(blank=True, decimal_places=2, help_text='Base courier rate', max_digits=10, null=True, validators=[django.core.validators.MinValueValidator(0)]),
        ),
        migrations.AddField(
            model_name='shippingchargehistory',
            name='commission',
            field=models.DecimalField(blank=True, decimal_places=2, help_text='Shipping charge commission amount', max_digits=10, null=True, validators=[django.core.validators.MinValueValidator(0)]),
        ),
        migrations.AlterField(
            model_name='shippingchargehistory',
            name='paid_by',
            field=models.CharField(choices=[('merchant', 'Merchant'), ('customer', 'Customer')], default='merchant', help_text='Who paid the shipping charge', max_length=20),
        ),
    ]
