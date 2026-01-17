# Generated manually for adding shipping_charge_commission field

from django.db import migrations, models
import django.core.validators


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0020_user_is_edit_access'),
    ]

    operations = [
        migrations.AddField(
            model_name='supersetting',
            name='shipping_charge_commission',
            field=models.IntegerField(
                default=10,
                help_text='Shipping charge commission percentage (added to courier rates)',
                validators=[
                    django.core.validators.MinValueValidator(0),
                    django.core.validators.MaxValueValidator(100)
                ]
            ),
        ),
    ]
