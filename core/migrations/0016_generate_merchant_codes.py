# Generated manually - Data migration to generate merchant codes for existing merchants

from django.db import migrations


def generate_merchant_codes(apps, schema_editor):
    User = apps.get_model('core', 'User')
    merchants = User.objects.filter(is_merchant=True, merchant_code__isnull=True).order_by('id')
    
    count = 0
    for merchant in merchants:
        count += 1
        code = f"MSB{count}"
        # Ensure uniqueness
        while User.objects.filter(merchant_code=code).exists():
            count += 1
            code = f"MSB{count}"
        merchant.merchant_code = code
        merchant.save(update_fields=['merchant_code'])


def reverse_generate_merchant_codes(apps, schema_editor):
    # No need to reverse - codes can stay
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0015_user_merchant_code'),
    ]

    operations = [
        migrations.RunPython(generate_merchant_codes, reverse_generate_merchant_codes),
    ]

