from django.core.management.base import BaseCommand
from django.template.loader import render_to_string
from core.models import Company, Investment, Deposit, CustomUser, Wallet

class Command(BaseCommand):
    help = 'Test admin dashboard template rendering'

    def handle(self, *args, **options):
        try:
            # Create minimal context data
            context = {
                'tier_stats': [],
                'total_deposits': 0,
                'total_investments': 0,
                'total_returns': 0,
                'total_users': 0,
                'user_details': [],
                'recent_deposits': [],
                'recent_investments': [],
                'recent_returns': [],
            }
            
            # Try to render the template with minimal context
            html = render_to_string('core/admin_dashboard.html', context)
            self.stdout.write(
                self.style.SUCCESS(f'Template rendered successfully! HTML length: {len(html)} characters')
            )
            
            # Test with some real data
            companies = Company.objects.all()[:2]  # Just first 2 companies
            users = CustomUser.objects.all()[:2]   # Just first 2 users
            
            # Create some sample tier_stats
            tier_stats = []
            for company in companies:
                tier_stats.append({
                    'tier': company,
                    'total_investments': 1,
                    'total_invested': 100,
                    'total_returns': 200,
                    'active_investments': 1
                })
            
            # Create some sample user_details
            user_details = []
            for user in users:
                wallet = Wallet.objects.filter(user=user).first()
                user_details.append({
                    'user': user,
                    'wallet': wallet,
                    'total_deposited': 500,
                    'total_invested': 100,
                    'total_returns': 200,
                    'active_investments': [],
                    'referral_earnings': 50,
                    'total_referrals': 2,
                    'deposits': [],
                    'investments': [],
                    'referrals': [],
                })
            
            # Create context with real data
            context_with_data = {
                'tier_stats': tier_stats,
                'total_deposits': 1000,
                'total_investments': 5,
                'total_returns': 2000,
                'total_users': users.count(),
                'user_details': user_details,
                'recent_deposits': [],
                'recent_investments': [],
                'recent_returns': [],
            }
            
            # Try to render the template with real data
            html_with_data = render_to_string('core/admin_dashboard.html', context_with_data)
            self.stdout.write(
                self.style.SUCCESS(f'Template with data rendered successfully! HTML length: {len(html_with_data)} characters')
            )
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error during template rendering: {str(e)}')
            )
            import traceback
            traceback.print_exc()