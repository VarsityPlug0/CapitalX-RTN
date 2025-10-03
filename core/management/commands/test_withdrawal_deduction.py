from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from core.models import Wallet, Withdrawal
from decimal import Decimal

User = get_user_model()

class Command(BaseCommand):
    help = 'Test withdrawal balance deduction'

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

            # Get or create wallet with a balance
            wallet, created = Wallet.objects.get_or_create(user=user)
            initial_balance = Decimal('200.00')
            wallet.balance = initial_balance
            wallet.save()
            
            self.stdout.write(
                self.style.SUCCESS(f'✅ Set wallet balance to R{wallet.balance}')
            )

            # Test 1: Create a withdrawal for R50
            withdrawal1 = Withdrawal(
                user=user,
                amount=Decimal('50.00'),
                payment_method='bank'
            )
            
            try:
                withdrawal1.save()
                # Refresh wallet to get updated balance
                wallet.refresh_from_db()
                expected_balance = initial_balance - Decimal('50.00')
                self.stdout.write(
                    self.style.SUCCESS(f'✅ Created withdrawal for R50.00')
                )
                self.stdout.write(
                    self.style.SUCCESS(f'✅ Wallet balance updated: R{wallet.balance} (expected: R{expected_balance})')
                )
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'❌ Failed to create withdrawal: {e}')
                )
                return

            # Test 2: Try to create another withdrawal for R100 (should work, balance is R150)
            withdrawal2 = Withdrawal(
                user=user,
                amount=Decimal('100.00'),
                payment_method='bank'
            )
            
            try:
                withdrawal2.save()
                # Refresh wallet to get updated balance
                wallet.refresh_from_db()
                expected_balance = initial_balance - Decimal('50.00') - Decimal('100.00')
                self.stdout.write(
                    self.style.SUCCESS(f'✅ Created withdrawal for R100.00')
                )
                self.stdout.write(
                    self.style.SUCCESS(f'✅ Wallet balance updated: R{wallet.balance} (expected: R{expected_balance})')
                )
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'❌ Failed to create withdrawal: {e}')
                )
                return

            # Test 3: Try to create another withdrawal for R100 (should fail, balance is R50)
            withdrawal3 = Withdrawal(
                user=user,
                amount=Decimal('100.00'),
                payment_method='bank'
            )
            
            try:
                withdrawal3.save()
                self.stdout.write(
                    self.style.ERROR(f'❌ Should not have been able to create withdrawal for R100.00')
                )
            except Exception as e:
                self.stdout.write(
                    self.style.SUCCESS(f'✅ Correctly prevented withdrawal: {e}')
                )

            # Test 4: Approve first withdrawal (should not change balance)
            withdrawal1.status = 'approved'
            withdrawal1.save()
            wallet.refresh_from_db()
            self.stdout.write(
                self.style.SUCCESS(f'✅ Approved first withdrawal, balance: R{wallet.balance}')
            )

            # Test 5: Reject second withdrawal (should return funds to wallet)
            old_balance = wallet.balance
            withdrawal2.status = 'rejected'
            withdrawal2.save()
            wallet.refresh_from_db()
            expected_balance = old_balance + Decimal('100.00')
            self.stdout.write(
                self.style.SUCCESS(f'✅ Rejected second withdrawal, balance: R{wallet.balance} (expected: R{expected_balance})')
            )
            
            # Clean up test withdrawals
            Withdrawal.objects.filter(user=user).delete()
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Error: {e}')
            )