# Generated manually

from django.db import migrations, models
import django.core.validators


class Migration(migrations.Migration):

    dependencies = [
        ('ecommerce', '0024_add_product_url_to_popup'),
        ('core', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='store',
            name='take_shipping_responsibility',
            field=models.BooleanField(default=False, help_text='Whether this store takes responsibility for shipping charges'),
        ),
        migrations.AddField(
            model_name='store',
            name='minimum_order_value',
            field=models.DecimalField(decimal_places=2, default=0, help_text='Minimum order value required for this store', max_digits=10, validators=[django.core.validators.MinValueValidator(0)]),
        ),
        migrations.CreateModel(
            name='ShippingChargeHistory',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('shipping_charge', models.DecimalField(decimal_places=2, help_text='Shipping charge amount', max_digits=10, validators=[django.core.validators.MinValueValidator(0)])),
                ('paid_by', models.CharField(choices=[('merchant', 'Merchant'), ('customer', 'Customer')], help_text='Who paid the shipping charge', max_length=20)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('customer', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='shipping_charge_history', to='core.user')),
                ('merchant', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='shipping_charge_history', to='ecommerce.store')),
                ('order', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='shipping_charge_history', to='ecommerce.order')),
            ],
            options={
                'verbose_name': 'Shipping Charge History',
                'verbose_name_plural': 'Shipping Charge Histories',
                'ordering': ['-created_at'],
            },
        ),
    ]
