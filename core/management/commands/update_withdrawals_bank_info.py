"""
Management command to update all withdrawals to use a specific bank account
"""

from django.core.management.base import BaseCommand
from core.models import Withdrawal

class Command(BaseCommand):
    help = 'Update all withdrawals to use a specific bank account'

    def add_arguments(self, parser):
        parser.add_argument('--bank-name', type=str, default='DISCOVERY', help='Bank name code')
        parser.add_argument('--account-holder', type=str, default='CapitalX Platform', help='Account holder name')
        parser.add_argument('--account-number', type=str, default='17856296290', help='Account number')
        parser.add_argument('--branch-code', type=str, default='679000', help='Branch code')
        parser.add_argument('--account-type', type=str, default='Savings Account', help='Account type')
        parser.add_argument('--bic-swift', type=str, default='DISCZAJJXXX', help='BIC/SWIFT code')

    def handle(self, *args, **options):
        # Bank account details
        bank_info = {
            'bank_name': options['bank_name'],
            'account_holder_name': options['account_holder'],
            'account_number': options['account_number'],
            'branch_code': options['branch_code'],
            'account_type': options['account_type'],
            'bic_swift': options['bic_swift']
        }
        
        self.stdout.write("Updating all withdrawals to use specified bank account:")
        self.stdout.write(f"  Account Holder: {bank_info['account_holder_name']}")
        self.stdout.write(f"  Bank: {bank_info['bank_name']}")
        self.stdout.write(f"  Account Number: {bank_info['account_number']}")
        self.stdout.write(f"  Branch Code: {bank_info['branch_code']}")
        self.stdout.write(f"  Account Type: {bank_info['account_type']}")
        self.stdout.write(f"  BIC/SWIFT: {bank_info['bic_swift']}")
        
        # Get all withdrawals
        all_withdrawals = Withdrawal.objects.all()
        total_withdrawals = all_withdrawals.count()
        
        self.stdout.write(f"\nFound {total_withdrawals} withdrawals to update")
        
        # Update each withdrawal
        updated_count = 0
        for withdrawal in all_withdrawals:
            withdrawal.bank_name = bank_info['bank_name']
            withdrawal.account_holder_name = bank_info['account_holder_name']
            withdrawal.account_number = bank_info['account_number']
            withdrawal.branch_code = bank_info['branch_code']
            withdrawal.account_type = bank_info['account_type']
            withdrawal.save()
            updated_count += 1
            self.stdout.write(f"  Updated withdrawal #{withdrawal.id}")
        
        self.stdout.write(
            self.style.SUCCESS(
                f"\nSuccessfully updated {updated_count} withdrawals to use the specified bank account"
            )
        )