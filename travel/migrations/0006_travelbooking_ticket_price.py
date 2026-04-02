# Generated manually for travel booking ticket_price snapshot

from django.core.validators import MinValueValidator
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('travel', '0005_travelbooking_cancelled_and_commission_distributed'),
    ]

    operations = [
        migrations.AddField(
            model_name='travelbooking',
            name='ticket_price',
            field=models.DecimalField(
                blank=True,
                decimal_places=2,
                help_text='Customer fare (vehicle.seat_price) at time of booking',
                max_digits=10,
                null=True,
                validators=[MinValueValidator(0)],
            ),
        ),
    ]
