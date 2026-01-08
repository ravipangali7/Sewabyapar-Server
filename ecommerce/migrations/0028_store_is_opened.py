# Generated manually

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ecommerce', '0027_rename_ecommerce_m_user_id_idx_ecommerce_m_user_id_3bcbaf_idx_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='store',
            name='is_opened',
            field=models.BooleanField(default=True, help_text='Whether the store is open for business. Only admins can change this.'),
        ),
    ]
