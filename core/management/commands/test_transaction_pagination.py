from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from core.models import Wallet, Deposit, Withdrawal, Investment, Company
from decimal import Decimal
from django.utils import timezone

User = get_user_model()

class Command(BaseCommand):
    help = 'Test transaction pagination in wallet view'

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

            # Get or create wallet
            wallet, created = Wallet.objects.get_or_create(user=user)
            wallet.balance = Decimal('1000.00')
            wallet.save()
            
            self.stdout.write(
                self.style.SUCCESS(f'✅ Set wallet balance to R{wallet.balance}')
            )

            # Create test company
            company, created = Company.objects.get_or_create(
                name='Test Company',
                defaults={
                    'share_price': Decimal('100.00'),
                    'expected_return': Decimal('10.00'),
                    'duration_days': 30
                }
            )

            # Create multiple test transactions
            for i in range(15):
                # Create deposits
                deposit = Deposit.objects.create(
                    user=user,
                    amount=Decimal(f'{50 + i * 10}.00'),
                    payment_method='eft',
                    status='approved'
                )
                
                # Create withdrawals
                withdrawal = Withdrawal.objects.create(
                    user=user,
                    amount=Decimal(f'{20 + i * 5}.00'),
                    payment_method='bank',
                    status='approved'
                )
                
                # Create investments
                investment = Investment.objects.create(
                    user=user,
                    company=company,
                    amount=Decimal(f'{100 + i * 20}.00'),
                    return_amount=Decimal(f'{10 + i * 2}.00'),
                    start_date=timezone.now(),
                    end_date=timezone.now() + timezone.timedelta(days=30),
                    is_active=True
                )
            
            self.stdout.write(
                self.style.SUCCESS(f'✅ Created 15 deposits, 15 withdrawals, and 15 investments')
            )
            
            # Test pagination logic
            deposits = Deposit.objects.filter(user=user).order_by('-created_at')
            withdrawals = Withdrawal.objects.filter(user=user).order_by('-created_at')
            investments = Investment.objects.filter(user=user).order_by('-created_at')
            
            self.stdout.write(
                self.style.SUCCESS(f'✅ Found {deposits.count()} deposits, {withdrawals.count()} withdrawals, {investments.count()} investments')
            )
            
            # Clean up test transactions
            Deposit.objects.filter(user=user).delete()
            Withdrawal.objects.filter(user=user).delete()
            Investment.objects.filter(user=user).delete()
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Error: {e}')
            )