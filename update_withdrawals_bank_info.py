#!/usr/bin/env python
"""
Script to update all withdrawals to use the specific Discovery Bank account for deposits
"""

import os
import sys
import django

# Add the project directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'safechain_ai.settings')
django.setup()

from core.models import Withdrawal

def update_withdrawals_bank_info():
    """
    Update all withdrawals to use the specific Discovery Bank account
    """
    # Discovery Bank account details
    discovery_bank_info = {
        'bank_name': 'DISCOVERY',
        'account_holder_name': 'CapitalX Platform',
        'account_number': '17856296290',
        'branch_code': '679000',
        'account_type': 'Savings Account',
        'bic_swift': 'DISCZAJJXXX'
    }
    
    print("Updating all withdrawals to use Discovery Bank account:")
    print(f"  Account Holder: {discovery_bank_info['account_holder_name']}")
    print(f"  Bank: {discovery_bank_info['bank_name']}")
    print(f"  Account Number: {discovery_bank_info['account_number']}")
    print(f"  Branch Code: {discovery_bank_info['branch_code']}")
    print(f"  Account Type: {discovery_bank_info['account_type']}")
    print(f"  BIC/SWIFT: {discovery_bank_info['bic_swift']}")
    
    # Get all withdrawals
    all_withdrawals = Withdrawal.objects.all()
    total_withdrawals = all_withdrawals.count()
    
    print(f"\nFound {total_withdrawals} withdrawals to update")
    
    # Update each withdrawal
    updated_count = 0
    for withdrawal in all_withdrawals:
        withdrawal.bank_name = discovery_bank_info['bank_name']
        withdrawal.account_holder_name = discovery_bank_info['account_holder_name']
        withdrawal.account_number = discovery_bank_info['account_number']
        withdrawal.branch_code = discovery_bank_info['branch_code']
        withdrawal.account_type = discovery_bank_info['account_type']
        withdrawal.save()
        updated_count += 1
        print(f"  Updated withdrawal #{withdrawal.id}")
    
    print(f"\nSuccessfully updated {updated_count} withdrawals to use the Discovery Bank account")

if __name__ == "__main__":
    update_withdrawals_bank_info()