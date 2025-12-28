# Generated manually - Data migration to generate item codes for existing products

from django.db import migrations


def generate_item_codes(apps, schema_editor):
    Product = apps.get_model('ecommerce', 'Product')
    products = Product.objects.filter(item_code__isnull=True).order_by('id')
    
    count = 0
    for product in products:
        count += 1
        code = f"PSB{count}"
        # Ensure uniqueness
        while Product.objects.filter(item_code=code).exists():
            count += 1
            code = f"PSB{count}"
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

