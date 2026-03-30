# Generated manually for platform travel commission ledger rows

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0004_transaction_related_travel_booking_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='transaction',
            name='user',
            field=models.ForeignKey(
                blank=True,
                help_text='Null for platform/system ledger rows (e.g. travel system commission)',
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name='transactions',
                to='core.user',
            ),
        ),
    ]
