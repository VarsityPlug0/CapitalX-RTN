from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from core.models import EFTBankAccount

User = get_user_model()

class Command(BaseCommand):
    help = 'Test bank account rotation for EFT deposits'

    def handle(self, *args, **options):
        # Create or get test users
        users = []
        for i in range(5):
            user, created = User.objects.get_or_create(
                email=f'testuser{i}@example.com',
                defaults={
                    'username': f'testuser{i}',
                    'first_name': f'Test',
                    'last_name': f'User{i}'
                }
            )
            if created:
                user.set_password('testpass123')
                user.save()
            users.append(user)
        
        self.stdout.write(
            self.style.SUCCESS('Created/Retrieved 5 test users')
        )
        
        # Test bank account rotation
        self.stdout.write('\nBank Account Rotation Test:')
        self.stdout.write('=' * 50)
        
        for user in users:
            account = EFTBankAccount.get_rotated_account(user.id)
            self.stdout.write(
                f'User ID {user.id:2d} ({user.email:20s}) -> {account["bank_name"]:15s} ({account["account_holder"]})'
            )
        
        self.stdout.write('\n' + '=' * 50)
        self.stdout.write(
            self.style.SUCCESS('Bank account rotation test completed successfully!')
        )