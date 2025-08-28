"""
Automated Email Lead System for CapitalX Investment Platform
===========================================================

This module provides a comprehensive lead generation and outreach system that:
1. Generates email addresses from names and domains
2. Validates email addresses (syntax, MX records, SMTP checks)
3. Creates personalized investment documents (PDF)
4. Sends automated emails with attachments
5. Tracks and logs all activities
6. Integrates seamlessly with Django models

Author: CapitalX Development Team
Version: 1.0
"""

import re
import os
import csv
import json
import socket
import smtplib
import logging
from typing import List, Dict, Tuple, Optional
from datetime import datetime
from pathlib import Path

# Django imports
from django.conf import settings
from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from django.utils import timezone

# Third-party imports for document generation
try:
    from reportlab.lib.pagesizes import letter, A4
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.lib import colors
    from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT
    HAS_REPORTLAB = True
except ImportError:
    HAS_REPORTLAB = False
    print("Warning: reportlab not installed. Install with: pip install reportlab")

try:
    import dns.resolver
    HAS_DNS = True
except ImportError:
    HAS_DNS = False
    print("Warning: dnspython not installed. Install with: pip install dnspython")


class EmailLeadSystem:
    """
    Main class for the automated email lead system.
    Handles email generation, validation, document creation, and sending.
    """
    
    def __init__(self, config: Optional[Dict] = None):
        """
        Initialize the lead system with configuration.
        
        Args:
            config (dict): Configuration dictionary with system settings
        """
        self.config = config or self._get_default_config()
        self.logger = self._setup_logging()
        self.leads_folder = Path(self.config['leads_folder'])
        self.leads_folder.mkdir(exist_ok=True)
        
        # Create subdirectories
        (self.leads_folder / 'documents').mkdir(exist_ok=True)
        (self.leads_folder / 'logs').mkdir(exist_ok=True)
        
    def _get_default_config(self) -> Dict:
        """Get default configuration settings."""
        return {
            'leads_folder': 'leads_system',
            'email_patterns': [
                '{first}.{last}@{domain}',
                '{first_initial}{last}@{domain}',
                '{first}{last_initial}@{domain}',
                '{first}@{domain}',
                '{last}@{domain}',
                '{first}_{last}@{domain}',
                '{first}-{last}@{domain}',
                '{first}{last}@{domain}',
            ],
            'smtp_settings': {
                'host': getattr(settings, 'EMAIL_HOST', 'smtp.gmail.com'),
                'port': getattr(settings, 'EMAIL_PORT', 587),
                'username': getattr(settings, 'EMAIL_HOST_USER', ''),
                'password': getattr(settings, 'EMAIL_HOST_PASSWORD', ''),
                'use_tls': getattr(settings, 'EMAIL_USE_TLS', True),
            },
            'sender_email': getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@capitalx.com'),
            'sender_name': 'CapitalX Investment Team',
            'email_subject': 'Exclusive Investment Opportunity - CapitalX Platform',
            'validate_mx_records': True,
            'validate_smtp': False,  # Set to True for deeper validation (slower)
            'max_leads_per_batch': 100,
            'document_template': 'investment_proposal',
        }
    
    def _setup_logging(self) -> logging.Logger:
        """Set up logging for the lead system."""
        logger = logging.getLogger('capitalx_leads')
        logger.setLevel(logging.INFO)
        
        # Create file handler
        log_file = self.leads_folder / 'logs' / f'leads_{datetime.now().strftime("%Y%m%d")}.log'
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.INFO)
        
        # Create formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        file_handler.setFormatter(formatter)
        
        # Add handler if not already added
        if not logger.handlers:
            logger.addHandler(file_handler)
        
        return logger
    
    def generate_email_addresses(self, first_name: str, last_name: str, domain: str) -> List[str]:
        """
        Generate multiple email address patterns for a person and domain.
        
        Args:
            first_name (str): Person's first name
            last_name (str): Person's last name
            domain (str): Email domain (e.g., 'company.com')
            
        Returns:
            List[str]: List of generated email addresses
        """
        first = first_name.lower().strip()
        last = last_name.lower().strip()
        first_initial = first[0] if first else ''
        last_initial = last[0] if last else ''
        
        emails = []
        
        for pattern in self.config['email_patterns']:
            try:
                email = pattern.format(
                    first=first,
                    last=last,
                    first_initial=first_initial,
                    last_initial=last_initial,
                    domain=domain.lower().strip()
                )
                emails.append(email)
            except (KeyError, IndexError):
                continue
        
        # Remove duplicates while preserving order
        return list(dict.fromkeys(emails))
    
    def validate_email_syntax(self, email: str) -> bool:
        """
        Validate email address syntax using regex.
        
        Args:
            email (str): Email address to validate
            
        Returns:
            bool: True if syntax is valid
        """
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, email))
    
    def validate_domain_mx(self, domain: str) -> bool:
        """
        Check if domain has MX records (can receive email).
        
        Args:
            domain (str): Domain to check
            
        Returns:
            bool: True if domain has MX records
        """
        if not HAS_DNS:
            self.logger.warning("DNS validation skipped - dnspython not installed")
            return True
        
        try:
            mx_records = dns.resolver.resolve(domain, 'MX')
            return len(mx_records) > 0
        except (dns.resolver.NXDOMAIN, dns.resolver.NoAnswer, Exception):
            return False
    
    def validate_email_smtp(self, email: str) -> bool:
        """
        Validate email by connecting to SMTP server (optional, slower).
        
        Args:
            email (str): Email address to validate
            
        Returns:
            bool: True if email appears valid via SMTP
        """
        if not self.config['validate_smtp']:
            return True
        
        domain = email.split('@')[1]
        
        try:
            # Get MX record
            if HAS_DNS:
                mx_records = dns.resolver.resolve(domain, 'MX')
                mx_record = str(mx_records[0].exchange)
            else:
                mx_record = domain
            
            # Connect to SMTP server
            server = smtplib.SMTP(timeout=10)
            server.connect(mx_record)
            server.helo('example.com')
            server.mail('test@example.com')
            code, message = server.rcpt(email)
            server.quit()
            
            return code == 250
        except Exception:
            return False
    
    def validate_email(self, email: str) -> Dict[str, bool]:
        """
        Comprehensive email validation.
        
        Args:
            email (str): Email address to validate
            
        Returns:
            Dict[str, bool]: Validation results
        """
        results = {
            'email': email,
            'syntax_valid': self.validate_email_syntax(email),
            'mx_valid': False,
            'smtp_valid': False,
            'overall_valid': False
        }
        
        if results['syntax_valid']:
            domain = email.split('@')[1]
            results['mx_valid'] = self.validate_domain_mx(domain)
            
            if results['mx_valid']:
                results['smtp_valid'] = self.validate_email_smtp(email)
        
        # Email is valid if syntax and MX are good
        results['overall_valid'] = results['syntax_valid'] and results['mx_valid']
        
        return results
    
    def create_investment_document(self, lead_data: Dict) -> Optional[str]:
        """
        Create a personalized investment document (PDF) for a lead.
        
        Args:
            lead_data (dict): Lead information including name, email, etc.
            
        Returns:
            str: Path to generated document, or None if failed
        """
        if not HAS_REPORTLAB:
            self.logger.error("Cannot create PDF - reportlab not installed")
            return None
        
        try:
            # Generate filename
            safe_name = f"{lead_data['first_name']}_{lead_data['last_name']}".replace(' ', '_')
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"investment_proposal_{safe_name}_{timestamp}.pdf"
            filepath = self.leads_folder / 'documents' / filename
            
            # Create PDF document
            doc = SimpleDocTemplate(str(filepath), pagesize=A4)
            story = []
            styles = getSampleStyleSheet()
            
            # Custom styles
            title_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Heading1'],
                fontSize=24,
                spaceAfter=30,
                alignment=TA_CENTER,
                textColor=colors.HexColor('#2E86AB')
            )
            
            heading_style = ParagraphStyle(
                'CustomHeading',
                parent=styles['Heading2'],
                fontSize=16,
                spaceAfter=12,
                textColor=colors.HexColor('#A23B72')
            )
            
            body_style = ParagraphStyle(
                'CustomBody',
                parent=styles['Normal'],
                fontSize=11,
                spaceAfter=12,
                alignment=TA_JUSTIFY
            )
            
            # Document content
            story.append(Paragraph("CapitalX Investment Platform", title_style))
            story.append(Spacer(1, 20))
            
            # Personalized greeting
            greeting = f"Dear {lead_data['first_name']} {lead_data['last_name']},"
            story.append(Paragraph(greeting, heading_style))
            story.append(Spacer(1, 12))
            
            # Investment proposal content
            content = f"""
            We are excited to present you with an exclusive investment opportunity through CapitalX, 
            South Africa's premier AI-powered investment platform.
            
            <b>Why Choose CapitalX?</b><br/>
            • Advanced AI trading algorithms with proven returns<br/>
            • Multiple investment plans from R60 to R10,000<br/>
            • Returns ranging from 67% to 500% based on your investment duration<br/>
            • Secure, regulated platform with full transparency<br/>
            • Real-time portfolio tracking and instant withdrawals<br/>
            
            <b>Investment Plans Available:</b><br/>
            <b>Phase 1 (Quick Returns):</b><br/>
            • Shoprite Plan: R60 → R100 in 12 hours (67% return)<br/>
            • Mr Price Plan: R100 → R200 in 24 hours (100% return)<br/>
            • Capitec Plan: R500 → R1,500 in 3 days (200% return)<br/>
            
            <b>Phase 2 (Balanced Growth):</b><br/>
            • MTN Plan: R1,000 → R4,000 in 1 week (300% return)<br/>
            • Vodacom Plan: R2,000 → R8,000 in 2 weeks (300% return)<br/>
            • Discovery Plan: R3,000 → R12,000 in 3 weeks (300% return)<br/>
            
            <b>Phase 3 (Premium Returns):</b><br/>
            • Sasol Plan: R4,000 → R15,000 in 1 month (275% return)<br/>
            • Standard Bank Plan: R5,000 → R20,000 in 1 month (300% return)<br/>
            • Naspers Plan: R10,000 → R50,000 in 2 months (400% return)<br/>
            
            <b>Special Features:</b><br/>
            • R10 referral bonus for every friend you invite<br/>
            • Professional email support and notifications<br/>
            • Mobile-responsive platform for trading on the go<br/>
            • Secure wallet system with real-time balance updates<br/>
            
            <b>Getting Started:</b><br/>
            1. Register at our platform using your email: {lead_data['email']}<br/>
            2. Verify your account via email<br/>
            3. Make your first deposit (minimum R50)<br/>
            4. Choose an investment plan that suits your goals<br/>
            5. Watch your investment grow with our AI algorithms<br/>
            
            This exclusive opportunity is available for a limited time. Our AI-powered system 
            has consistently delivered exceptional returns to our investors, and we believe 
            you would be an excellent addition to our growing community.
            
            <b>Next Steps:</b><br/>
            To claim your spot and start investing, simply visit our platform and register 
            with the email address this proposal was sent to. Our team will be available 
            to guide you through the process and answer any questions you may have.
            
            We look forward to welcoming you to the CapitalX family and helping you achieve 
            your financial goals through smart, AI-driven investments.
            """
            
            story.append(Paragraph(content, body_style))
            story.append(Spacer(1, 20))
            
            # Contact information
            contact_info = """
            <b>Contact Information:</b><br/>
            Email: mkhabeleenterprise@gmail.com<br/>
            Platform: https://capitalx-platform.onrender.com<br/>
            Admin Support: Available 24/7 through our platform<br/>
            
            <i>CapitalX Investment Platform - Your Gateway to AI-Powered Financial Growth</i>
            """
            
            story.append(Paragraph(contact_info, body_style))
            
            # Build PDF
            doc.build(story)
            
            self.logger.info(f"Created investment document: {filename}")
            return str(filepath)
            
        except Exception as e:
            self.logger.error(f"Failed to create document for {lead_data['email']}: {str(e)}")
            return None
    
    def send_email_with_attachment(self, to_email: str, lead_data: Dict, 
                                 attachment_path: Optional[str] = None) -> bool:
        """
        Send personalized email with investment document attachment.
        
        Args:
            to_email (str): Recipient email address
            lead_data (dict): Lead information for personalization
            attachment_path (str): Path to document attachment
            
        Returns:
            bool: True if email sent successfully
        """
        try:
            # Create personalized email content
            subject = self.config['email_subject']
            
            # Email body
            email_body = f"""
Dear {lead_data['first_name']} {lead_data['last_name']},

Greetings from the CapitalX Investment Team!

We hope this message finds you well. We are reaching out to present you with an exclusive investment opportunity that could significantly enhance your financial portfolio.

CapitalX is South Africa's leading AI-powered investment platform, and we have carefully selected you as a potential investor based on your profile and interests. Our advanced algorithms have consistently delivered exceptional returns to our growing community of successful investors.

🎯 **Why This Opportunity is Perfect for You:**

• **Proven Track Record**: Our AI trading system has delivered consistent profits with returns up to 500%
• **Flexible Investment Options**: Choose from 9 different plans ranging from R60 to R10,000
• **Quick Returns**: See profits in as little as 12 hours with our short-term plans
• **Secure Platform**: Fully regulated with transparent operations and real-time tracking
• **Professional Support**: Dedicated team available 24/7 to assist you

📋 **Your Personalized Investment Proposal:**

We have prepared a detailed investment proposal document specifically for you, which is attached to this email. This document contains:

✅ Complete breakdown of all available investment plans
✅ Expected returns and timeframes for each option
✅ Step-by-step guide to get started
✅ Special bonuses and referral opportunities
✅ Platform features and security measures

🚀 **Ready to Start Investing?**

Getting started is simple:
1. Review the attached investment proposal
2. Visit our platform and register with this email address
3. Verify your account and make your first deposit
4. Choose an investment plan that aligns with your goals
5. Watch your investment grow with our AI-powered system

💡 **Limited Time Opportunity:**

This exclusive invitation is time-sensitive. Our AI system has identified current market conditions as particularly favorable, making this an optimal time to begin your investment journey with CapitalX.

We believe that you have the potential to achieve significant financial growth through our platform, and we would be honored to have you join our community of successful investors.

If you have any questions or would like to discuss this opportunity further, please don't hesitate to reach out to our team. We are here to support you every step of the way.

Best regards,

The CapitalX Investment Team
Email: mkhabeleenterprise@gmail.com
Platform: https://capitalx-platform.onrender.com

---
*This email was sent to {to_email} as part of our exclusive investor outreach program. 
CapitalX is committed to helping individuals achieve their financial goals through innovative, AI-driven investment solutions.*
            """
            
            # Create email message
            msg = EmailMessage(
                subject=subject,
                body=email_body,
                from_email=f"{self.config['sender_name']} <{self.config['sender_email']}>",
                to=[to_email],
            )
            
            # Attach document if provided
            if attachment_path and os.path.exists(attachment_path):
                with open(attachment_path, 'rb') as f:
                    msg.attach(
                        f"CapitalX_Investment_Proposal_{lead_data['first_name']}_{lead_data['last_name']}.pdf",
                        f.read(),
                        'application/pdf'
                    )
            
            # Send email
            msg.send()
            
            self.logger.info(f"Email sent successfully to {to_email}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to send email to {to_email}: {str(e)}")
            return False
    
    def process_lead(self, first_name: str, last_name: str, domain: str) -> Dict:
        """
        Process a single lead: generate emails, validate, create document, send email.
        
        Args:
            first_name (str): Lead's first name
            last_name (str): Lead's last name
            domain (str): Target domain
            
        Returns:
            Dict: Processing results
        """
        lead_data = {
            'first_name': first_name,
            'last_name': last_name,
            'domain': domain,
            'timestamp': timezone.now().isoformat(),
            'processed_emails': [],
            'valid_emails': [],
            'documents_created': [],
            'emails_sent': [],
            'success': False
        }
        
        try:
            # Generate email addresses
            email_addresses = self.generate_email_addresses(first_name, last_name, domain)
            lead_data['generated_emails'] = email_addresses
            
            # Validate each email
            for email in email_addresses:
                validation_result = self.validate_email(email)
                lead_data['processed_emails'].append(validation_result)
                
                if validation_result['overall_valid']:
                    lead_data['valid_emails'].append(email)
            
            # Process valid emails
            for email in lead_data['valid_emails'][:3]:  # Limit to first 3 valid emails
                email_lead_data = lead_data.copy()
                email_lead_data['email'] = email
                
                # Create personalized document
                document_path = self.create_investment_document(email_lead_data)
                if document_path:
                    lead_data['documents_created'].append(document_path)
                
                # Send email with attachment
                email_sent = self.send_email_with_attachment(
                    email, email_lead_data, document_path
                )
                
                if email_sent:
                    lead_data['emails_sent'].append(email)
            
            # Mark as successful if any emails were sent
            lead_data['success'] = len(lead_data['emails_sent']) > 0
            
        except Exception as e:
            self.logger.error(f"Error processing lead {first_name} {last_name}: {str(e)}")
            lead_data['error'] = str(e)
        
        return lead_data
    
    def process_lead_batch(self, leads: List[Dict]) -> List[Dict]:
        """
        Process a batch of leads.
        
        Args:
            leads (List[Dict]): List of lead dictionaries with first_name, last_name, domain
            
        Returns:
            List[Dict]: Processing results for each lead
        """
        results = []
        total_leads = len(leads)
        
        self.logger.info(f"Starting batch processing of {total_leads} leads")
        
        for i, lead in enumerate(leads[:self.config['max_leads_per_batch']], 1):
            self.logger.info(f"Processing lead {i}/{total_leads}: {lead['first_name']} {lead['last_name']}")
            
            result = self.process_lead(
                lead['first_name'],
                lead['last_name'],
                lead['domain']
            )
            
            results.append(result)
        
        # Save results to CSV
        self.save_results_to_csv(results)
        
        self.logger.info(f"Batch processing completed. {len(results)} leads processed.")
        return results
    
    def save_results_to_csv(self, results: List[Dict]) -> str:
        """
        Save processing results to CSV file.
        
        Args:
            results (List[Dict]): Lead processing results
            
        Returns:
            str: Path to CSV file
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        csv_filename = f"lead_results_{timestamp}.csv"
        csv_path = self.leads_folder / 'logs' / csv_filename
        
        try:
            with open(csv_path, 'w', newline='', encoding='utf-8') as csvfile:
                fieldnames = [
                    'first_name', 'last_name', 'domain', 'timestamp',
                    'generated_emails_count', 'valid_emails_count',
                    'documents_created_count', 'emails_sent_count',
                    'success', 'valid_emails', 'emails_sent'
                ]
                
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                
                for result in results:
                    row = {
                        'first_name': result['first_name'],
                        'last_name': result['last_name'],
                        'domain': result['domain'],
                        'timestamp': result['timestamp'],
                        'generated_emails_count': len(result.get('generated_emails', [])),
                        'valid_emails_count': len(result.get('valid_emails', [])),
                        'documents_created_count': len(result.get('documents_created', [])),
                        'emails_sent_count': len(result.get('emails_sent', [])),
                        'success': result['success'],
                        'valid_emails': '; '.join(result.get('valid_emails', [])),
                        'emails_sent': '; '.join(result.get('emails_sent', []))
                    }
                    writer.writerow(row)
            
            self.logger.info(f"Results saved to CSV: {csv_filename}")
            return str(csv_path)
            
        except Exception as e:
            self.logger.error(f"Failed to save results to CSV: {str(e)}")
            return ""


def create_sample_leads() -> List[Dict]:
    """Create sample leads for testing the system."""
    return [
        {'first_name': 'John', 'last_name': 'Smith', 'domain': 'gmail.com'},
        {'first_name': 'Sarah', 'last_name': 'Johnson', 'domain': 'outlook.com'},
        {'first_name': 'Michael', 'last_name': 'Brown', 'domain': 'yahoo.com'},
        {'first_name': 'Emma', 'last_name': 'Davis', 'domain': 'hotmail.com'},
        {'first_name': 'David', 'last_name': 'Wilson', 'domain': 'icloud.com'},
    ]


# Example usage and testing function
def test_lead_system():
    """Test the lead system with sample data."""
    print("Testing CapitalX Email Lead System...")
    
    # Initialize system
    lead_system = EmailLeadSystem()
    
    # Test email generation
    emails = lead_system.generate_email_addresses('John', 'Smith', 'example.com')
    print(f"Generated emails: {emails}")
    
    # Test email validation
    test_email = 'john.smith@gmail.com'
    validation = lead_system.validate_email(test_email)
    print(f"Validation result: {validation}")
    
    # Test with sample leads (uncomment to test)
    # sample_leads = create_sample_leads()
    # results = lead_system.process_lead_batch(sample_leads)
    # print(f"Processed {len(results)} leads")


if __name__ == "__main__":
    test_lead_system()
