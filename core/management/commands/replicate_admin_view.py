from django.core.management.base import BaseCommand
from core.models import Company, Investment, Deposit, CustomUser, Wallet, Referral, ReferralReward
from django.db.models import Sum

class Command(BaseCommand):
    help = 'Replicate exactly what the admin dashboard view does'

    def handle(self, *args, **options):
        try:
            self.stdout.write('Replicating admin dashboard view...')
            
            # Step 1: Get all tiers
            self.stdout.write('Step 1: Getting all tiers...')
            tiers = Company.objects.all().order_by('share_price')
            self.stdout.write(f'Found {tiers.count()} tiers')
            
            # Step 2: Get investment statistics for each tier
            self.stdout.write('Step 2: Getting investment statistics...')
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
            
            # Step 3: Get overall statistics
            self.stdout.write('Step 3: Getting overall statistics...')
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
            
            # Step 4: Get detailed user information
            self.stdout.write('Step 4: Getting detailed user information...')
            users = CustomUser.objects.all().order_by('-date_joined')
            self.stdout.write(f'Found {users.count()} users')
            
            user_details = []
            for i, user in enumerate(users):
                self.stdout.write(f'Processing user {i+1}: {user.email}')
                
                # Get user's wallet
                wallet = Wallet.objects.filter(user=user).first()
                self.stdout.write(f'  Wallet: {wallet}')
                
                # Get user's deposits
                deposits = Deposit.objects.filter(user=user).order_by('-created_at')
                total_deposited = deposits.filter(status='approved').aggregate(
                    total=Sum('amount')
                )['total'] or 0
                self.stdout.write(f'  Total deposited: {total_deposited}')
                
                # Get user's investments
                investments = Investment.objects.filter(user=user)
                total_invested = investments.aggregate(
                    total=Sum('amount')
                )['total'] or 0
                self.stdout.write(f'  Total invested: {total_invested}')
                
                # Get user's returns
                total_returns_user = investments.filter(is_active=False).aggregate(
                    total=Sum('return_amount')
                )['total'] or 0
                self.stdout.write(f'  Total returns: {total_returns_user}')
                
                # Get user's active investments
                active_investments = investments.filter(is_active=True)
                self.stdout.write(f'  Active investments count: {active_investments.count()}')
                
                # Get user's referral earnings
                referral_earnings = ReferralReward.objects.filter(referrer=user).aggregate(
                    total=Sum('reward_amount')
                )['total'] or 0
                self.stdout.write(f'  Referral earnings: {referral_earnings}')
                
                # Get user's referrals
                referrals = Referral.objects.filter(inviter=user)
                self.stdout.write(f'  Total referrals: {referrals.count()}')
                
                user_details.append({
                    'user': user,
                    'wallet': wallet,
                    'total_deposited': total_deposited,
                    'total_invested': total_invested,
                    'total_returns': total_returns_user,
                    'active_investments': active_investments,
                    'referral_earnings': referral_earnings,
                    'total_referrals': referrals.count(),
                    'deposits': deposits,
                    'investments': investments,
                    'referrals': referrals,
                })
            
            # Step 5: Get recent activities
            self.stdout.write('Step 5: Getting recent activities...')
            recent_deposits = Deposit.objects.all().order_by('-created_at')[:10]
            self.stdout.write(f'Found {recent_deposits.count()} recent deposits')
            
            recent_investments = Investment.objects.all().order_by('-created_at')[:10]
            self.stdout.write(f'Found {recent_investments.count()} recent investments')
            
            recent_returns = Investment.objects.filter(is_active=False).order_by('-end_date')[:10]
            self.stdout.write(f'Found {recent_returns.count()} recent returns')
            
            # Step 6: Create context
            self.stdout.write('Step 6: Creating context...')
            context = {
                'tier_stats': tier_stats,
                'total_deposits': total_deposits,
                'total_investments': total_investments,
                'total_returns': total_returns,
                'total_users': total_users,
                'user_details': user_details,
                'recent_deposits': recent_deposits,
                'recent_investments': recent_investments,
                'recent_returns': recent_returns,
            }
            
            # Step 7: Try to render the template
            self.stdout.write('Step 7: Rendering template...')
            from django.template.loader import render_to_string
            html = render_to_string('core/admin_dashboard.html', context)
            self.stdout.write(
                self.style.SUCCESS(f'Template rendered successfully! HTML length: {len(html)} characters')
            )
            
            self.stdout.write(
                self.style.SUCCESS('All steps completed successfully!')
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error during replication: {str(e)}')
            )
            import traceback
            traceback.print_exc()