from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
import getpass

User = get_user_model()


class Command(BaseCommand):
    help = 'Create a superuser with phone, email, name, and password'

    def add_arguments(self, parser):
        parser.add_argument(
            '--phone',
            type=str,
            help='Phone number (will be used as username)',
        )
        parser.add_argument(
            '--email',
            type=str,
            help='Email address',
        )
        parser.add_argument(
            '--name',
            type=str,
            help='Full name',
        )
        parser.add_argument(
            '--password',
            type=str,
            help='Password',
        )

    def handle(self, *args, **options):
        # Get phone number
        phone = options.get('phone')
        if not phone:
            phone = input('Phone: ')
        
        # Get email
        email = options.get('email')
        if not email:
            email = input('Email address: ')
        
        # Get name
        name = options.get('name')
        if not name:
            name = input('Name: ')
        
        # Get password
        password = options.get('password')
        if not password:
            password = getpass.getpass('Password: ')
            password_confirm = getpass.getpass('Password (again): ')
            if password != password_confirm:
                self.stdout.write(
                    self.style.ERROR('Error: Your passwords didn\'t match.')
                )
                return

        # Check if user already exists
        if User.objects.filter(phone=phone).exists():
            self.stdout.write(
                self.style.ERROR(f'Error: User with phone {phone} already exists.')
            )
            return

        try:
            # Create the superuser
            user = User.objects.create_superuser(
                phone=phone,
                email=email,
                name=name,
                password=password
            )
            
            self.stdout.write(
                self.style.SUCCESS(f'Successfully created superuser: {user.name} ({user.phone})')
            )
            
        except ValidationError as e:
            self.stdout.write(
                self.style.ERROR(f'Error: {e}')
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error creating user: {e}')
            )
