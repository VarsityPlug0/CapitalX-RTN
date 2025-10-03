from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from core.models import Withdrawal
from core.email_utils import send_admin_withdrawal_notification
from decimal import Decimal

User = get_user_model()

class Command(BaseCommand):
    help = 'Test admin withdrawal notification email'

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

            # Create a test withdrawal
            withdrawal = Withdrawal.objects.create(
                user=user,
                amount=Decimal('150.00'),
                payment_method='bank',
                account_holder_name='Test User',
                bank_name='FNB',
                account_number='1234567890',
                branch_code='250655',
                account_type='Cheque'
            )
            
            self.stdout.write(
                self.style.SUCCESS(f'✅ Created test withdrawal: R{withdrawal.amount}')
            )

            # Test sending admin withdrawal notification
            success = send_admin_withdrawal_notification(withdrawal)
            if success:
                self.stdout.write(
                    self.style.SUCCESS('✅ Admin withdrawal notification email sent successfully')
                )
            else:
                self.stdout.write(
                    self.style.ERROR('❌ Admin withdrawal notification email failed')
                )
            
            # Clean up test withdrawal
            withdrawal.delete()
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Error: {e}')
            )