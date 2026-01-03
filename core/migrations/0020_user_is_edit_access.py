# Generated manually for adding is_edit_access field

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0019_supersetting_payment_methods'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='is_edit_access',
            field=models.BooleanField(default=False, help_text='Whether merchant can edit store after creation (default False)'),
        ),
    ]
