from django.core.management.base import BaseCommand
from core.models import Company, Investment, Deposit, CustomUser, Wallet, Referral, ReferralReward
from django.db.models import Sum

class Command(BaseCommand):
    help = 'Debug user details section of admin dashboard'

    def handle(self, *args, **options):
        try:
            # Test the user details section
            self.stdout.write('Testing user details section...')
            
            # Get detailed user information
            users = CustomUser.objects.all().order_by('-date_joined')
            self.stdout.write(f'Found {users.count()} users')
            
            user_details = []
            
            for user in users:
                self.stdout.write(f'Processing user: {user.email}')
                
                # Get user's wallet
                wallet = Wallet.objects.filter(user=user).first()
                self.stdout.write(f'  Wallet balance: {wallet.balance if wallet else "No wallet"}')
                
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
                total_returns = investments.filter(is_active=False).aggregate(
                    total=Sum('return_amount')
                )['total'] or 0
                self.stdout.write(f'  Total returns: {total_returns}')
                
                # Get user's active investments
                active_investments = investments.filter(is_active=True)
                self.stdout.write(f'  Active investments: {active_investments.count()}')
                
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
                    'total_returns': total_returns,
                    'active_investments': active_investments,
                    'referral_earnings': referral_earnings,
                    'total_referrals': referrals.count(),
                    'deposits': deposits,
                    'investments': investments,
                    'referrals': referrals,
                })
            
            self.stdout.write(
                self.style.SUCCESS('User details section processed successfully!')
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error during user details processing: {str(e)}')
            )
            import traceback
            traceback.print_exc()