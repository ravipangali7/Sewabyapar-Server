# Generated manually for adding product field to Banner

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('ecommerce', '0022_generate_item_codes'),
    ]

    operations = [
        migrations.AddField(
            model_name='banner',
            name='product',
            field=models.ForeignKey(blank=True, help_text='Product to navigate to when banner is clicked (takes priority over URL)', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='banners', to='ecommerce.product'),
        ),
        migrations.AlterField(
            model_name='banner',
            name='url',
            field=models.URLField(blank=True, help_text='URL to navigate when banner is clicked (ignored if product is selected)', null=True),
        ),
    ]

