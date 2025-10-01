from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from core.models import Deposit, AdminActivityLog
from datetime import datetime

User = get_user_model()

class Command(BaseCommand):
    help = 'Approve a deposit by ID, bypassing normal validation'

    def add_arguments(self, parser):
        parser.add_argument('deposit_id', type=int, help='ID of the deposit to approve')
        parser.add_argument('--admin-email', type=str, help='Email of admin user to log activity (optional)')

    def handle(self, *args, **options):
        deposit_id = options['deposit_id']
        admin_email = options.get('admin_email', 'system@capitalx.com')
        
        try:
            # Get the deposit
            deposit = Deposit.objects.get(id=deposit_id)
            
            if deposit.status != 'pending':
                self.stdout.write(
                    self.style.ERROR(f'Deposit {deposit_id} is not pending approval (status: {deposit.status}).')
                )
                return
            
            # Get admin user for logging
            try:
                admin_user = User.objects.get(email=admin_email)
            except User.DoesNotExist:
                # Create a system user if needed
                admin_user = User.objects.create_user(
                    username='system_approver',
                    email=admin_email,
                    password='system_pass_123',
                    is_staff=True
                )
                self.stdout.write(f'Created system admin user: {admin_email}')
            
            # Approve the deposit
            old_status = deposit.status
            deposit.status = 'approved'
            deposit.admin_notes += f'\nApproved by system command on {datetime.now().strftime("%Y-%m-%d %H:%M")}'
            deposit.save()
            
            # Log admin activity
            AdminActivityLog.objects.create(
                admin_user=admin_user,
                action='System Approved Deposit',
                target_model='Deposit',
                target_id=deposit.id,
                details=f'System approved deposit of R{deposit.amount} for user {deposit.user.username} via management command'
            )
            
            self.stdout.write(
                self.style.SUCCESS(f'Successfully approved deposit {deposit_id} (R{deposit.amount}) for {deposit.user.username}')
            )
            
        except Deposit.DoesNotExist:
            self.stdout.write(
                self.style.ERROR(f'Deposit {deposit_id} not found.')
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error approving deposit: {str(e)}')
            )