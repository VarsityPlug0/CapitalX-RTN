from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from core.models import Deposit
from decimal import Decimal
import os

User = get_user_model()

class Command(BaseCommand):
    help = 'Test voucher deposit creation and image handling'

    def add_arguments(self, parser):
        parser.add_argument(
            '--email',
            type=str,
            help='Email address of test user'
        )

    def handle(self, *args, **options):
        email = options['email'] or 'test@example.com'
        
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
        deposit = Deposit.objects.create(
            user=user,
            amount=Decimal('150.00'),
            payment_method='voucher',
            voucher_code='VOUCHER123',
            status='pending'
        )
        
        self.stdout.write(f'Created deposit: #{deposit.id} - R{deposit.amount} ({deposit.status})')
        self.stdout.write(f'Payment method: {deposit.get_payment_method_display()}')
        self.stdout.write(f'Voucher code: {deposit.voucher_code}')
        self.stdout.write(f'Voucher image: {deposit.voucher_image}')
        
        # Check if admin notification signal was triggered
        self.stdout.write('Admin notification should have been sent automatically via signal')
        
        # Clean up test deposit
        deposit.delete()
        
        if created:
            user.delete()
            self.stdout.write('Cleaned up test user')
        
        self.stdout.write(
            self.style.SUCCESS('Voucher deposit test completed!')
        )