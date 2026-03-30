# Generated manually for travel booking lifecycle and payout idempotency

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('travel', '0004_travelbooking_qr_code'),
    ]

    operations = [
        migrations.AddField(
            model_name='travelbooking',
            name='commission_distributed',
            field=models.BooleanField(
                default=False,
                help_text='Set when boarding payout and ledger entries are completed',
            ),
        ),
        migrations.AlterField(
            model_name='travelbooking',
            name='status',
            field=models.CharField(
                choices=[
                    ('pending', 'Pending'),
                    ('booked', 'Booked'),
                    ('boarded', 'Boarded'),
                    ('cancelled', 'Cancelled'),
                ],
                default='pending',
                max_length=20,
            ),
        ),
    ]
