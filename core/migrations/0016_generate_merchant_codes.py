# Generated manually - Data migration to generate merchant codes for existing merchants

from django.db import migrations


def generate_merchant_codes(apps, schema_editor):
    User = apps.get_model('core', 'User')
    merchants = User.objects.filter(is_merchant=True, merchant_code__isnull=True).order_by('id')
    
    # Determine the starting count for new codes
    max_code_number = 0
    existing_merchants_with_codes = User.objects.filter(is_merchant=True).exclude(merchant_code__isnull=True).filter(merchant_code__startswith='MSB')
    for merchant in existing_merchants_with_codes:
        if merchant.merchant_code and merchant.merchant_code.startswith('MSB'):
            try:
                # Extract number after "MSB" prefix (3 characters)
                num = int(merchant.merchant_code[3:])
                if num > max_code_number:
                    max_code_number = num
            except ValueError:
                pass  # Ignore codes that don't match the pattern
    
    count = max_code_number
    for merchant in merchants:
        count += 1
        code = f"MSB{count:02d}"  # Zero-padded to 2 digits
        # Ensure uniqueness
        while User.objects.filter(merchant_code=code).exists():
            count += 1
            code = f"MSB{count:02d}"
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

