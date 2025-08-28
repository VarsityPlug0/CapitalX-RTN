"""
Django management command to test the Email Lead System

Usage:
python manage.py test_lead_system
python manage.py test_lead_system --create-sample-data
python manage.py test_lead_system --process-leads
"""

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from core.models import LeadCampaign, Lead
from core.lead_system import EmailLeadSystem


class Command(BaseCommand):
    help = 'Test the Email Lead System functionality'

    def add_arguments(self, parser):
        parser.add_argument(
            '--create-sample-data',
            action='store_true',
            help='Create sample campaign and leads for testing',
        )
        parser.add_argument(
            '--process-leads',
            action='store_true',
            help='Process pending leads in test campaign',
        )
        parser.add_argument(
            '--validate-only',
            action='store_true',
            help='Only test email validation without sending emails',
        )

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS('🚀 Testing CapitalX Email Lead System')
        )

        if options['create_sample_data']:
            self.create_sample_data()

        if options['process_leads']:
            self.process_test_leads()

        if options['validate_only']:
            self.test_email_validation()

        if not any([options['create_sample_data'], options['process_leads'], options['validate_only']]):
            self.run_basic_tests()

    def create_sample_data(self):
        """Create sample campaign and leads for testing"""
        self.stdout.write('Creating sample test data...')
        
        # Get or create admin user
        User = get_user_model()
        admin_user = User.objects.filter(is_superuser=True).first()
        
        if not admin_user:
            self.stdout.write(
                self.style.ERROR('No admin user found. Please create an admin user first.')
            )
            return

        # Create test campaign
        campaign, created = LeadCampaign.objects.get_or_create(
            name='Test Campaign - Lead System',
            defaults={
                'description': 'Automated test campaign for the email lead system',
                'created_by': admin_user,
                'is_active': True
            }
        )

        if created:
            self.stdout.write(
                self.style.SUCCESS(f'✅ Created test campaign: {campaign.name}')
            )
        else:
            self.stdout.write(f'📋 Using existing campaign: {campaign.name}')

        # Sample leads with various domains
        sample_leads = [
            {'first_name': 'John', 'last_name': 'Smith', 'domain': 'gmail.com'},
            {'first_name': 'Sarah', 'last_name': 'Johnson', 'domain': 'outlook.com'},
            {'first_name': 'Michael', 'last_name': 'Brown', 'domain': 'yahoo.com'},
            {'first_name': 'Emma', 'last_name': 'Davis', 'domain': 'hotmail.com'},
            {'first_name': 'David', 'last_name': 'Wilson', 'domain': 'icloud.com'},
            {'first_name': 'Lisa', 'last_name': 'Taylor', 'domain': 'test.com'},  # Invalid domain for testing
        ]

        leads_created = 0
        for lead_data in sample_leads:
            lead, created = Lead.objects.get_or_create(
                campaign=campaign,
                first_name=lead_data['first_name'],
                last_name=lead_data['last_name'],
                domain=lead_data['domain'],
                defaults={'status': 'pending'}
            )
            
            if created:
                leads_created += 1

        # Update campaign totals
        campaign.total_leads = campaign.leads.count()
        campaign.save()

        self.stdout.write(
            self.style.SUCCESS(
                f'✅ Created {leads_created} new test leads. '
                f'Total leads in campaign: {campaign.total_leads}'
            )
        )

    def process_test_leads(self):
        """Process pending leads in test campaign"""
        campaign = LeadCampaign.objects.filter(
            name='Test Campaign - Lead System'
        ).first()

        if not campaign:
            self.stdout.write(
                self.style.ERROR('❌ Test campaign not found. Run with --create-sample-data first.')
            )
            return

        pending_leads = campaign.leads.filter(status='pending')
        
        if not pending_leads.exists():
            self.stdout.write(
                self.style.WARNING('⚠️ No pending leads found in test campaign.')
            )
            return

        self.stdout.write(f'🔄 Processing {pending_leads.count()} pending leads...')

        # Initialize lead system
        lead_system = EmailLeadSystem()

        # Convert to lead system format
        leads_data = []
        for lead in pending_leads:
            leads_data.append({
                'first_name': lead.first_name,
                'last_name': lead.last_name,
                'domain': lead.domain
            })

        # Process leads
        results = lead_system.process_lead_batch(leads_data)

        # Display results
        for i, result in enumerate(results):
            lead = pending_leads[i]
            status = "✅ Success" if result['success'] else "❌ Failed"
            
            self.stdout.write(
                f"  {status} {lead.first_name} {lead.last_name} @ {lead.domain}"
            )
            
            if result['valid_emails']:
                self.stdout.write(f"    📧 Valid emails: {', '.join(result['valid_emails'])}")
            
            if result['emails_sent']:
                self.stdout.write(f"    ✉️ Emails sent: {len(result['emails_sent'])}")
            
            if result.get('error'):
                self.stdout.write(f"    ❌ Error: {result['error']}")

        successful = sum(1 for r in results if r['success'])
        self.stdout.write(
            self.style.SUCCESS(
                f"\n🎯 Processing complete: {successful}/{len(results)} leads successful"
            )
        )

    def test_email_validation(self):
        """Test email validation functionality only"""
        self.stdout.write('🔍 Testing email validation...')

        lead_system = EmailLeadSystem()

        # Test various email formats
        test_cases = [
            ('John', 'Smith', 'gmail.com'),
            ('Sarah', 'Johnson', 'outlook.com'),
            ('Test', 'User', 'invalid-domain.xyz'),
            ('', '', 'gmail.com'),  # Empty names
        ]

        for first_name, last_name, domain in test_cases:
            if not first_name or not last_name:
                continue
                
            self.stdout.write(f"\n👤 Testing: {first_name} {last_name} @ {domain}")

            # Generate emails
            emails = lead_system.generate_email_addresses(first_name, last_name, domain)
            self.stdout.write(f"  📧 Generated {len(emails)} email patterns")

            # Validate first few emails
            for email in emails[:3]:
                validation = lead_system.validate_email(email)
                status = "✅" if validation['overall_valid'] else "❌"
                
                details = []
                if validation['syntax_valid']:
                    details.append("syntax✓")
                if validation['mx_valid']:
                    details.append("mx✓")
                    
                self.stdout.write(f"    {status} {email} ({', '.join(details)})")

    def run_basic_tests(self):
        """Run basic functionality tests"""
        self.stdout.write('🧪 Running basic functionality tests...')

        lead_system = EmailLeadSystem()

        # Test 1: Email generation
        self.stdout.write('\n1️⃣ Testing email generation...')
        emails = lead_system.generate_email_addresses('John', 'Smith', 'example.com')
        self.stdout.write(f"   ✅ Generated {len(emails)} email patterns")
        for email in emails[:3]:
            self.stdout.write(f"      📧 {email}")

        # Test 2: Email validation
        self.stdout.write('\n2️⃣ Testing email validation...')
        test_email = 'john.smith@gmail.com'
        validation = lead_system.validate_email(test_email)
        
        status = "✅ Valid" if validation['overall_valid'] else "❌ Invalid"
        self.stdout.write(f"   {status} {test_email}")
        self.stdout.write(f"      Syntax: {'✓' if validation['syntax_valid'] else '✗'}")
        self.stdout.write(f"      MX Record: {'✓' if validation['mx_valid'] else '✗'}")

        # Test 3: Configuration
        self.stdout.write('\n3️⃣ Testing system configuration...')
        self.stdout.write(f"   📁 Leads folder: {lead_system.leads_folder}")
        self.stdout.write(f"   📧 Email patterns: {len(lead_system.config['email_patterns'])}")
        self.stdout.write(f"   🔧 SMTP host: {lead_system.config['smtp_settings']['host']}")

        self.stdout.write(
            self.style.SUCCESS('\n🎉 Basic tests completed successfully!')
        )
        
        self.stdout.write(
            '\n📖 Usage examples:\n'
            '  python manage.py test_lead_system --create-sample-data\n'
            '  python manage.py test_lead_system --validate-only\n'
            '  python manage.py test_lead_system --process-leads\n'
        )
