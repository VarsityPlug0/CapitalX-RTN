from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from core.email_utils import (
    send_welcome_email, 
    send_deposit_confirmation, 
    send_withdrawal_confirmation,
    send_referral_bonus,
    send_security_alert,
    send_custom_email
)
from core.models import Deposit, Withdrawal
from decimal import Decimal

User = get_user_model()

class Command(BaseCommand):
    help = 'Test email functionality by sending test emails'

    def add_arguments(self, parser):
        parser.add_argument(
            '--email',
            type=str,
            help='Email address to send test emails to'
        )
        parser.add_argument(
            '--type',
            type=str,
            choices=['welcome', 'deposit', 'withdrawal', 'referral', 'security', 'custom', 'all'],
            default='all',
            help='Type of email to test'
        )

    def handle(self, *args, **options):
        email = options['email']
        email_type = options['type']
        
        if not email:
            self.stdout.write(
                self.style.ERROR('Please provide an email address with --email')
            )
            return
        
        # Get or create a test user
        user, created = User.objects.get_or_create(
            email=email,
            defaults={
                'username': email,
                'first_name': 'Test',
                'last_name': 'User',
                'phone': '1234567890'
            }
        )
        
        if created:
            user.set_password('testpass123')
            user.save()
            self.stdout.write(f'Created test user: {user.email}')
        else:
            self.stdout.write(f'Using existing user: {user.email}')
        
        # Test different email types
        if email_type == 'welcome' or email_type == 'all':
            self.test_welcome_email(user)
        
        if email_type == 'deposit' or email_type == 'all':
            self.test_deposit_email(user)
        
        if email_type == 'withdrawal' or email_type == 'all':
            self.test_withdrawal_email(user)
        
        if email_type == 'referral' or email_type == 'all':
            self.test_referral_email(user)
        
        if email_type == 'security' or email_type == 'all':
            self.test_security_email(user)
        
        if email_type == 'custom' or email_type == 'all':
            self.test_custom_email(user)
        
        self.stdout.write(
            self.style.SUCCESS('Email testing completed!')
        )

    def test_welcome_email(self, user):
        """Test welcome email"""
        try:
            success = send_welcome_email(user)
            if success:
                self.stdout.write(
                    self.style.SUCCESS('✅ Welcome email sent successfully')
                )
            else:
                self.stdout.write(
                    self.style.ERROR('❌ Welcome email failed')
                )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Welcome email error: {e}')
            )

    def test_deposit_email(self, user):
        """Test deposit confirmation email"""
        try:
            # Create a test deposit
            deposit = Deposit.objects.create(
                user=user,
                amount=Decimal('100.00'),
                payment_method='card',
                cardholder_name='Test User',
                card_last4='1234'
            )
            
            success = send_deposit_confirmation(user, deposit)
            if success:
                self.stdout.write(
                    self.style.SUCCESS('✅ Deposit confirmation email sent successfully')
                )
            else:
                self.stdout.write(
                    self.style.ERROR('❌ Deposit confirmation email failed')
                )
            
            # Clean up test deposit
            deposit.delete()
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Deposit email error: {e}')
            )

    def test_withdrawal_email(self, user):
        """Test withdrawal confirmation email"""
        try:
            # Create a test withdrawal
            withdrawal = Withdrawal.objects.create(
                user=user,
                amount=Decimal('50.00'),
                payment_method='bank'
            )
            
            success = send_withdrawal_confirmation(user, withdrawal)
            if success:
                self.stdout.write(
                    self.style.SUCCESS('✅ Withdrawal confirmation email sent successfully')
                )
            else:
                self.stdout.write(
                    self.style.ERROR('❌ Withdrawal confirmation email failed')
                )
            
            # Clean up test withdrawal
            withdrawal.delete()
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Withdrawal email error: {e}')
            )

    def test_referral_email(self, user):
        """Test referral bonus email"""
        try:
            # Create a test referral user
            referral_user, created = User.objects.get_or_create(
                email='referral@test.com',
                defaults={
                    'username': 'referral@test.com',
                    'first_name': 'Referral',
                    'last_name': 'User',
                    'phone': '0987654321'
                }
            )
            
            success = send_referral_bonus(user, referral_user, Decimal('25.00'))
            if success:
                self.stdout.write(
                    self.style.SUCCESS('✅ Referral bonus email sent successfully')
                )
            else:
                self.stdout.write(
                    self.style.ERROR('❌ Referral bonus email failed')
                )
            
            # Clean up test referral user
            if created:
                referral_user.delete()
                
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Referral email error: {e}')
            )

    def test_security_email(self, user):
        """Test security alert email"""
        try:
            success = send_security_alert(
                user, 
                'Login from New Device', 
                'We detected a login from a new device in Johannesburg, South Africa.'
            )
            if success:
                self.stdout.write(
                    self.style.SUCCESS('✅ Security alert email sent successfully')
                )
            else:
                self.stdout.write(
                    self.style.ERROR('❌ Security alert email failed')
                )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Security email error: {e}')
            )

    def test_custom_email(self, user):
        """Test custom email"""
        try:
            success = send_custom_email(
                user.email,
                'Test Custom Email',
                'core/emails/welcome_email.html',
                {'user': user, 'site_name': 'CapitalX Test'}
            )
            if success:
                self.stdout.write(
                    self.style.SUCCESS('✅ Custom email sent successfully')
                )
            else:
                self.stdout.write(
                    self.style.ERROR('❌ Custom email failed')
                )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Custom email error: {e}')
            )
