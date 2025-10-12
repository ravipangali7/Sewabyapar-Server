from django.core.management.base import BaseCommand
from django.utils import timezone
from core.models import User, Store, Category, Product, Coupon
from decimal import Decimal


class Command(BaseCommand):
    help = 'Populate the database with sample data'

    def handle(self, *args, **options):
        self.stdout.write('Creating sample data...')

        # Create sample users
        user1, created = User.objects.get_or_create(
            phone='+1234567890',
            defaults={
                'name': 'John Doe',
                'email': 'vendor1@example.com'
            }
        )
        if created:
            user1.set_password('password123')
            user1.save()

        user2, created = User.objects.get_or_create(
            phone='+1234567891',
            defaults={
                'name': 'Jane Smith',
                'email': 'vendor2@example.com'
            }
        )
        if created:
            user2.set_password('password123')
            user2.save()

        # Create sample stores
        store1, created = Store.objects.get_or_create(
            name='Tech Store',
            defaults={
                'description': 'Latest technology and gadgets',
                'owner': user1,
                'address': '123 Tech Street, Silicon Valley, CA 94000',
                'phone': '+1-555-0123',
                'email': 'info@techstore.com'
            }
        )

        store2, created = Store.objects.get_or_create(
            name='Fashion Hub',
            defaults={
                'description': 'Trendy fashion and accessories',
                'owner': user2,
                'address': '456 Fashion Ave, New York, NY 10001',
                'phone': '+1-555-0456',
                'email': 'info@fashionhub.com'
            }
        )

        # Create sample categories
        electronics, created = Category.objects.get_or_create(
            name='Electronics',
            defaults={'description': 'Electronic devices and gadgets'}
        )

        clothing, created = Category.objects.get_or_create(
            name='Clothing',
            defaults={'description': 'Fashion and apparel'}
        )

        laptops, created = Category.objects.get_or_create(
            name='Laptops',
            defaults={
                'description': 'Portable computers',
                'parent': electronics
            }
        )

        smartphones, created = Category.objects.get_or_create(
            name='Smartphones',
            defaults={
                'description': 'Mobile phones and accessories',
                'parent': electronics
            }
        )

        mens_clothing, created = Category.objects.get_or_create(
            name="Men's Clothing",
            defaults={
                'description': 'Clothing for men',
                'parent': clothing
            }
        )

        womens_clothing, created = Category.objects.get_or_create(
            name="Women's Clothing",
            defaults={
                'description': 'Clothing for women',
                'parent': clothing
            }
        )

        # Create sample products
        products_data = [
            {
                'name': 'MacBook Pro 16"',
                'description': 'Powerful laptop for professionals',
                'store': store1,
                'category': laptops,
                'price': Decimal('2499.99'),
                'compare_price': Decimal('2799.99'),
                'sku': 'MBP16-001',
                'stock_quantity': 50,
                'is_featured': True
            },
            {
                'name': 'iPhone 15 Pro',
                'description': 'Latest iPhone with advanced features',
                'store': store1,
                'category': smartphones,
                'price': Decimal('999.99'),
                'compare_price': Decimal('1099.99'),
                'sku': 'IP15P-001',
                'stock_quantity': 100,
                'is_featured': True
            },
            {
                'name': 'Dell XPS 13',
                'description': 'Ultrabook with excellent performance',
                'store': store1,
                'category': laptops,
                'price': Decimal('1299.99'),
                'sku': 'DXP13-001',
                'stock_quantity': 75
            },
            {
                'name': 'Men\'s Casual T-Shirt',
                'description': 'Comfortable cotton t-shirt',
                'store': store2,
                'category': mens_clothing,
                'price': Decimal('29.99'),
                'compare_price': Decimal('39.99'),
                'sku': 'MCT-001',
                'stock_quantity': 200,
                'is_featured': True
            },
            {
                'name': 'Women\'s Summer Dress',
                'description': 'Elegant summer dress',
                'store': store2,
                'category': womens_clothing,
                'price': Decimal('79.99'),
                'sku': 'WSD-001',
                'stock_quantity': 150
            },
            {
                'name': 'Men\'s Jeans',
                'description': 'Classic blue jeans',
                'store': store2,
                'category': mens_clothing,
                'price': Decimal('59.99'),
                'sku': 'MJ-001',
                'stock_quantity': 100
            }
        ]

        for product_data in products_data:
            Product.objects.get_or_create(
                sku=product_data['sku'],
                defaults=product_data
            )

        # Create sample coupons
        coupons_data = [
            {
                'code': 'WELCOME10',
                'description': 'Welcome discount for new customers',
                'discount_type': 'percentage',
                'discount_value': Decimal('10.00'),
                'minimum_amount': Decimal('50.00'),
                'usage_limit': 100,
                'valid_from': timezone.now(),
                'valid_until': timezone.now() + timezone.timedelta(days=30)
            },
            {
                'code': 'SAVE20',
                'description': 'Save $20 on orders over $100',
                'discount_type': 'fixed',
                'discount_value': Decimal('20.00'),
                'minimum_amount': Decimal('100.00'),
                'usage_limit': 50,
                'valid_from': timezone.now(),
                'valid_until': timezone.now() + timezone.timedelta(days=15)
            }
        ]

        for coupon_data in coupons_data:
            Coupon.objects.get_or_create(
                code=coupon_data['code'],
                defaults=coupon_data
            )

        self.stdout.write(
            self.style.SUCCESS('Successfully created sample data!')
        )
        self.stdout.write('Sample users created:')
        self.stdout.write('- +1234567890 / password123 (John Doe)')
        self.stdout.write('- +1234567891 / password123 (Jane Smith)')
        self.stdout.write('You can use these credentials to test the API.')
