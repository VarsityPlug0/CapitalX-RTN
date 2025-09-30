from django.core.management.base import BaseCommand
from core.models import CustomUser, Wallet

class Command(BaseCommand):
    help = 'Ensure all users have wallets'

    def handle(self, *args, **options):
        users = CustomUser.objects.all()
        self.stdout.write(f'Checking wallets for {users.count()} users...')
        
        for user in users:
            wallet, created = Wallet.objects.get_or_create(user=user)
            if created:
                self.stdout.write(
                    self.style.SUCCESS(f'Created wallet for user: {user.email}')
                )
            else:
                self.stdout.write(f'User {user.email} already has a wallet')
        
        self.stdout.write(
            self.style.SUCCESS('All users have wallets now!')
        )