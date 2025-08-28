"""
Management command to test email templates and URLs
"""
from django.core.management.base import BaseCommand
from django.template.loader import render_to_string
from core.email_utils import get_site_url


class Command(BaseCommand):
    help = 'Test email templates and verify all URLs are correct'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('🔧 Testing Email Templates and URLs'))
        
        # Test site URL configuration
        site_url = get_site_url()
        self.stdout.write(f"✅ Site URL: {site_url}")
        
        # Test email templates that contain links
        templates_to_test = [
            'core/emails/welcome_email.html',
            'core/emails/account_verification.html',
            'core/emails/deposit_approved.html',
            'core/emails/deposit_rejected.html',
            'core/emails/referral_bonus.html',
            'core/emails/security_alert.html',
        ]
        
        test_context = {
            'site_url': site_url,
            'user': {
                'username': 'testuser',
                'first_name': 'Test',
                'last_name': 'User',
                'email': 'test@example.com'
            },
            'verification_url': f'{site_url}/verify-email/test-token/',
            'reset_url': f'{site_url}/reset-password/test-token/',
            'referrer': {
                'username': 'referrer',
                'first_name': 'Referrer'
            },
            'referred_user': {
                'username': 'referred',
                'first_name': 'Referred'
            },
            'reward_amount': 10,
            'deposit_amount': 100,
            'deposit': {
                'amount': 100,
                'payment_method': 'Card',
                'created_at': '2024-01-01'
            }
        }
        
        self.stdout.write('\n📧 Testing Email Templates:')
        
        for template in templates_to_test:
            try:
                rendered = render_to_string(template, test_context)
                
                # Check if the production URL appears in the rendered template
                if site_url in rendered:
                    self.stdout.write(f"  ✅ {template}: URLs correctly point to {site_url}")
                else:
                    self.stdout.write(f"  ⚠️  {template}: May not contain production URLs")
                    
                # Check for any localhost references
                if 'localhost' in rendered:
                    self.stdout.write(f"  ❌ {template}: Contains localhost references!")
                
            except Exception as e:
                self.stdout.write(f"  ❌ {template}: Error - {str(e)}")
        
        # Test specific email functions
        self.stdout.write('\n🔗 Expected Button/Link URLs:')
        button_urls = [
            f'{site_url}/dashboard/',
            f'{site_url}/login/',
            f'{site_url}/wallet/',
            f'{site_url}/referral/',
            f'{site_url}/tiers/',
            f'{site_url}/deposit/',
            f'{site_url}/contact/',
            f'{site_url}/profile/',
            f'{site_url}/portfolio/',
            f'{site_url}/register/?ref=testuser',
            f'{site_url}/capitalx_admin/core/deposit/',
        ]
        
        for url in button_urls:
            self.stdout.write(f"  🔗 {url}")
        
        self.stdout.write('\n✅ Email URL testing completed!')
        self.stdout.write(f"🌐 All email buttons and links should now point to: {site_url}")
        
        return "Email URL testing completed successfully!"
