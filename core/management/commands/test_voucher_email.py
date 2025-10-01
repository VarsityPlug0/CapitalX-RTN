from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from core.email_utils import send_admin_deposit_notification
from core.models import Deposit
from decimal import Decimal
import os

User = get_user_model()

class Command(BaseCommand):
    help = 'Test voucher deposit notification email with image attachment'

    def add_arguments(self, parser):
        parser.add_argument(
            '--email',
            type=str,
            help='Email address to send test emails to'
        )
        parser.add_argument(
            '--with-image',
            action='store_true',
            help='Include a test image attachment'
        )

    def handle(self, *args, **options):
        email = options['email']
        with_image = options['with_image']
        
        if not email:
            self.stdout.write(
                self.style.ERROR('Please provide an email address with --email')
            )
            return
        
        # Get or create a test user
        user, created = User.objects.get_or_create(
            email=email,
            defaults={
                'username': email,
                'first_name': 'Test',
                'last_name': 'User',
                'phone': '1234567890'
            }
        )
        
        if created:
            user.set_password('testpass123')
            user.save()
            self.stdout.write(f'Created test user: {user.email}')
        else:
            self.stdout.write(f'Using existing user: {user.email}')
        
        # Create a test voucher deposit
        deposit_data = {
            'user': user,
            'amount': Decimal('150.00'),
            'payment_method': 'voucher',
            'voucher_code': 'VOUCHER123',
            'status': 'pending'
        }
        
        # Add a test image if requested
        if with_image:
            # Use a simple test image path (this would be a real image in production)
            test_image_path = 'core/static/images/logo.png'  # Using the logo as a test image
            if os.path.exists(test_image_path):
                deposit_data['voucher_image'] = test_image_path
                self.stdout.write(f'Using test image: {test_image_path}')
            else:
                self.stdout.write(
                    self.style.WARNING(f'Test image not found: {test_image_path}')
                )
        
        deposit = Deposit.objects.create(**deposit_data)
        
        # Test sending the admin notification
        try:
            success = send_admin_deposit_notification(deposit)
            if success:
                self.stdout.write(
                    self.style.SUCCESS('✅ Voucher deposit notification email sent successfully')
                )
            else:
                self.stdout.write(
                    self.style.ERROR('❌ Voucher deposit notification email failed')
                )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Voucher deposit notification error: {e}')
            )
        
        # Clean up test deposit
        deposit.delete()
        
        if created:
            user.delete()
            self.stdout.write('Cleaned up test user')
        
        self.stdout.write(
            self.style.SUCCESS('Voucher email testing completed!')
        )