from django.core.management.base import BaseCommand
from core.models import Company, Investment, Deposit, CustomUser, Wallet, Referral, ReferralReward

class Command(BaseCommand):
    help = 'Test admin dashboard data queries'

    def handle(self, *args, **options):
        try:
            # Test Company data
            self.stdout.write('Testing Company data...')
            companies = Company.objects.all()
            self.stdout.write(f'Found {companies.count()} companies')
            
            for company in companies:
                self.stdout.write(f'  - {company.name}: R{company.share_price}')
                
                # Test investment statistics
                total_investments = Investment.objects.filter(company=company).count()
                self.stdout.write(f'    Total investments: {total_investments}')
                
            # Test overall statistics
            self.stdout.write('\nTesting overall statistics...')
            total_deposits = Deposit.objects.filter(status='approved').count()
            self.stdout.write(f'Total approved deposits: {total_deposits}')
            
            total_investments = Investment.objects.count()
            self.stdout.write(f'Total investments: {total_investments}')
            
            total_users = CustomUser.objects.count()
            self.stdout.write(f'Total users: {total_users}')
            
            self.stdout.write(
                self.style.SUCCESS('All tests passed successfully!')
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error during testing: {str(e)}')
            )
            raise