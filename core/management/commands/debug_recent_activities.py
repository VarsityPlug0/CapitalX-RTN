from django.core.management.base import BaseCommand
from core.models import Deposit, Investment
from django.db.models import Sum

class Command(BaseCommand):
    help = 'Debug recent activities section of admin dashboard'

    def handle(self, *args, **options):
        try:
            # Test the recent activities section
            self.stdout.write('Testing recent activities section...')
            
            # Get recent activities
            recent_deposits = Deposit.objects.all().order_by('-created_at')[:10]
            self.stdout.write(f'Found {recent_deposits.count()} recent deposits')
            
            recent_investments = Investment.objects.all().order_by('-created_at')[:10]
            self.stdout.write(f'Found {recent_investments.count()} recent investments')
            
            recent_returns = Investment.objects.filter(is_active=False).order_by('-end_date')[:10]
            self.stdout.write(f'Found {recent_returns.count()} recent returns')
            
            # Test specific queries used in the view
            for deposit in recent_deposits:
                self.stdout.write(f'Deposit: {deposit.user.email} - R{deposit.amount} ({deposit.status})')
                
            for investment in recent_investments:
                self.stdout.write(f'Investment: {investment.user.email} - {investment.company.name} - R{investment.amount}')
                
            for return_item in recent_returns:
                self.stdout.write(f'Return: {return_item.user.email} - {return_item.company.name} - R{return_item.return_amount}')
            
            self.stdout.write(
                self.style.SUCCESS('Recent activities section processed successfully!')
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error during recent activities processing: {str(e)}')
            )
            import traceback
            traceback.print_exc()