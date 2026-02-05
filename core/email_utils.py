"""
Backward Compatibility Layer for Email System

This module re-exports all email functions from the new 'emails' app.
Any existing code that imports from core.email_utils will continue to work.

Usage remains unchanged:
    from core.email_utils import send_welcome_email, send_deposit_confirmation
    
Or import from the new location directly:
    from emails.services import send_welcome_email, send_deposit_confirmation
"""

# Re-export everything from the new emails.services module
from emails.services import (
    # Main EmailService class
    EmailService,
    
    # Convenience functions for sending specific email types
    send_welcome_email,
    send_deposit_confirmation,
    send_withdrawal_confirmation,
    send_referral_bonus,
    send_security_alert,
    send_custom_email,
    send_password_reset_email,
    send_account_verification,
    send_investment_update,
    send_otp_email,
    send_deposit_status_email,
    send_referral_bonus_email,
    
    # Admin notification functions
    send_admin_deposit_notification,
    send_admin_withdrawal_notification,
)

# For 'from core.email_utils import *' compatibility
__all__ = [
    'EmailService',
    'send_welcome_email',
    'send_deposit_confirmation',
    'send_withdrawal_confirmation',
    'send_referral_bonus',
    'send_security_alert',
    'send_custom_email',
    'send_password_reset_email',
    'send_account_verification',
    'send_investment_update',
    'send_otp_email',
    'send_deposit_status_email',
    'send_referral_bonus_email',
    'send_admin_deposit_notification',
    'send_admin_withdrawal_notification',
]
