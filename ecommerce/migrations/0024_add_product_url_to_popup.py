# Generated manually for adding product and url fields to Popup

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('ecommerce', '0023_add_product_to_banner'),
    ]

    operations = [
        migrations.AddField(
            model_name='popup',
            name='product',
            field=models.ForeignKey(blank=True, help_text='Product to navigate to when popup is clicked (takes priority over URL)', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='popups', to='ecommerce.product'),
        ),
        migrations.AddField(
            model_name='popup',
            name='url',
            field=models.URLField(blank=True, help_text='URL to navigate when popup is clicked (ignored if product is selected)', null=True),
        ),
    ]

