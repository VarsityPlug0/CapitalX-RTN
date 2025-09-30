from django.core.management.base import BaseCommand
from core.models import Company, Investment, Deposit, CustomUser, Wallet, Referral, ReferralReward
from django.db.models import Sum

class Command(BaseCommand):
    help = 'Debug admin dashboard context variables'

    def handle(self, *args, **options):
        try:
            # Test the exact queries used in admin_dashboard_view
            self.stdout.write('Testing admin dashboard context variables...')
            
            # Get all tiers
            tiers = Company.objects.all().order_by('share_price')
            self.stdout.write(f'Found {tiers.count()} tiers')
            
            # Get investment statistics for each tier
            tier_stats = []
            for tier in tiers:
                self.stdout.write(f'Processing tier: {tier.name}')
                
                # Get total number of investments for this tier
                total_investments = Investment.objects.filter(company=tier).count()
                self.stdout.write(f'  Total investments: {total_investments}')
                
                # Get total amount invested in this tier
                total_invested = Investment.objects.filter(company=tier).aggregate(
                    total=Sum('amount')
                )['total'] or 0
                self.stdout.write(f'  Total invested: {total_invested}')
                
                # Get total returns for this tier
                total_returns = Investment.objects.filter(company=tier).aggregate(
                    total=Sum('return_amount')
                )['total'] or 0
                self.stdout.write(f'  Total returns: {total_returns}')
                
                # Get active investments count
                active_investments = Investment.objects.filter(
                    company=tier,
                    is_active=True
                ).count()
                self.stdout.write(f'  Active investments: {active_investments}')
                
                tier_stats.append({
                    'tier': tier,
                    'total_investments': total_investments,
                    'total_invested': total_invested,
                    'total_returns': total_returns,
                    'active_investments': active_investments
                })
            
            # Get overall statistics
            self.stdout.write('\nTesting overall statistics...')
            total_deposits = Deposit.objects.filter(status='approved').aggregate(
                total=Sum('amount')
            )['total'] or 0
            self.stdout.write(f'Total deposits: {total_deposits}')
            
            total_investments = Investment.objects.count()
            self.stdout.write(f'Total investments: {total_investments}')
            
            total_returns = Investment.objects.filter(is_active=False).aggregate(
                total=Sum('return_amount')
            )['total'] or 0
            self.stdout.write(f'Total returns: {total_returns}')
            
            total_users = CustomUser.objects.count()
            self.stdout.write(f'Total users: {total_users}')
            
            self.stdout.write(
                self.style.SUCCESS('All context variables generated successfully!')
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error during context generation: {str(e)}')
            )
            import traceback
            traceback.print_exc()