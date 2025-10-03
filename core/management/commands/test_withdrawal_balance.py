from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from core.models import Wallet, Withdrawal
from decimal import Decimal

User = get_user_model()

class Command(BaseCommand):
    help = 'Test withdrawal balance validation'

    def add_arguments(self, parser):
        parser.add_argument('--email', type=str, help='Email of test user')

    def handle(self, *args, **options):
        email = options['email'] or 'testuser@example.com'
        
        try:
            # Get or create test user
            user, created = User.objects.get_or_create(
                email=email,
                defaults={
                    'username': email.split('@')[0],
                    'first_name': 'Test',
                    'last_name': 'User'
                }
            )
            
            if created:
                user.set_password('testpass123')
                user.save()
                self.stdout.write(
                    self.style.SUCCESS(f'✅ Created test user: {email}')
                )
            else:
                self.stdout.write(
                    self.style.SUCCESS(f'✅ Using existing user: {email}')
                )

            # Get or create wallet with a small balance
            wallet, created = Wallet.objects.get_or_create(user=user)
            wallet.balance = Decimal('100.00')
            wallet.save()
            
            self.stdout.write(
                self.style.SUCCESS(f'✅ Set wallet balance to R{wallet.balance}')
            )

            # Test 1: Try to withdraw more than balance
            withdrawal1 = Withdrawal(
                user=user,
                amount=Decimal('150.00'),
                payment_method='bank'
            )
            
            # This should fail in the view, but let's see what happens with direct model creation
            try:
                withdrawal1.save()
                self.stdout.write(
                    self.style.WARNING(f'⚠️  Created withdrawal for R150.00 (more than balance)')
                )
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'❌ Failed to create withdrawal: {e}')
                )

            # Test 2: Try to withdraw less than balance
            withdrawal2 = Withdrawal(
                user=user,
                amount=Decimal('50.00'),
                payment_method='bank'
            )
            
            try:
                withdrawal2.save()
                self.stdout.write(
                    self.style.SUCCESS(f'✅ Created withdrawal for R50.00 (less than balance)')
                )
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'❌ Failed to create withdrawal: {e}')
                )
            
            # Clean up test withdrawals
            Withdrawal.objects.filter(user=user).delete()
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Error: {e}')
            )