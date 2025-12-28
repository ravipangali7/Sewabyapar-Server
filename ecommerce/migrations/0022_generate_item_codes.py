# Generated manually - Data migration to generate item codes for existing products

from django.db import migrations


def generate_item_codes(apps, schema_editor):
    Product = apps.get_model('ecommerce', 'Product')
    products = Product.objects.filter(item_code__isnull=True).order_by('id')
    
    # Determine the starting count for new codes
    max_code_number = 0
    existing_products_with_codes = Product.objects.exclude(item_code__isnull=True).filter(item_code__startswith='PSB')
    for product in existing_products_with_codes:
        if product.item_code and product.item_code.startswith('PSB'):
            try:
                # Extract number after "PSB" prefix (3 characters)
                num = int(product.item_code[3:])
                if num > max_code_number:
                    max_code_number = num
            except ValueError:
                pass  # Ignore codes that don't match the pattern
    
    count = max_code_number
    for product in products:
        count += 1
        code = f"PSB{count:02d}"  # Zero-padded to 2 digits
        # Ensure uniqueness
        while Product.objects.filter(item_code=code).exists():
            count += 1
            code = f"PSB{count:02d}"
        product.item_code = code
        product.save(update_fields=['item_code'])


def reverse_generate_item_codes(apps, schema_editor):
    # No need to reverse - codes can stay
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('ecommerce', '0021_product_item_code'),
    ]

    operations = [
        migrations.RunPython(generate_item_codes, reverse_generate_item_codes),
    ]

