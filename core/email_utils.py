import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
from django.conf import settings
from django.core.mail import send_mail, EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags
import os
import logging

logger = logging.getLogger(__name__)

class EmailService:
    """Comprehensive email service for CapitalX application"""
    
    def __init__(self):
        self.smtp_server = getattr(settings, 'EMAIL_HOST', 'smtp.gmail.com')
        self.port = getattr(settings, 'EMAIL_PORT', 587)
        self.username = getattr(settings, 'EMAIL_HOST_USER', '')
        self.password = getattr(settings, 'EMAIL_HOST_PASSWORD', '')
        self.use_tls = getattr(settings, 'EMAIL_USE_TLS', True)
        self.default_from = getattr(settings, 'DEFAULT_FROM_EMAIL', self.username)
    
    def send_email(self, to_email, subject, html_content, text_content=None, attachments=None):
        """
        Send email using Django's built-in email backend
        
        Args:
            to_email (str): Recipient email address
            subject (str): Email subject
            html_content (str): HTML email content
            text_content (str, optional): Plain text version
            attachments (list, optional): List of file paths to attach
        """
        try:
            if text_content is None:
                text_content = strip_tags(html_content)
            
            if attachments:
                # Use EmailMultiAlternatives for attachments
                email = EmailMultiAlternatives(
                    subject=subject,
                    body=text_content,
                    from_email=self.default_from,
                    to=[to_email]
                )
                email.attach_alternative(html_content, "text/html")
                
                # Add attachments
                for attachment_path in attachments:
                    if os.path.exists(attachment_path):
                        with open(attachment_path, 'rb') as f:
                            email.attach_file(attachment_path)
                
                email.send()
            else:
                # Use simple send_mail for basic emails
                send_mail(
                    subject=subject,
                    message=text_content,
                    from_email=self.default_from,
                    recipient_list=[to_email],
                    html_message=html_content,
                    fail_silently=False
                )
            
            logger.info(f"Email sent successfully to {to_email}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send email to {to_email}: {str(e)}")
            return False
    
    def send_welcome_email(self, user):
        """Send welcome email to new users"""
        subject = "Welcome to CapitalX - Your Investment Journey Begins!"
        
        html_content = render_to_string('core/emails/welcome_email.html', {
            'user': user,
            'site_name': 'CapitalX'
        })
        
        return self.send_email(
            to_email=user.email,
            subject=subject,
            html_content=html_content
        )
    
    def send_password_reset_email(self, user, reset_url):
        """Send password reset email"""
        subject = "CapitalX - Password Reset Request"
        
        html_content = render_to_string('core/emails/password_reset.html', {
            'user': user,
            'reset_url': reset_url,
            'site_name': 'CapitalX'
        })
        
        return self.send_email(
            to_email=user.email,
            subject=subject,
            html_content=html_content
        )
    
    def send_deposit_confirmation(self, user, deposit):
        """Send deposit confirmation email"""
        subject = f"CapitalX - Deposit Confirmation (R{deposit.amount})"
        
        html_content = render_to_string('core/emails/deposit_confirmation.html', {
            'user': user,
            'deposit': deposit,
            'site_name': 'CapitalX'
        })
        
        return self.send_email(
            to_email=user.email,
            subject=subject,
            html_content=html_content
        )
    
    def send_withdrawal_confirmation(self, user, withdrawal):
        """Send withdrawal confirmation email"""
        subject = f"CapitalX - Withdrawal Confirmation (R{withdrawal.amount})"
        
        html_content = render_to_string('core/emails/withdrawal_confirmation.html', {
            'user': user,
            'withdrawal': withdrawal,
            'site_name': 'CapitalX'
        })
        
        return self.send_email(
            to_email=user.email,
            subject=subject,
            html_content=html_content
        )
    
    def send_investment_update(self, user, investment):
        """Send investment update email"""
        subject = "CapitalX - Investment Update"
        
        html_content = render_to_string('core/emails/investment_update.html', {
            'user': user,
            'investment': investment,
            'site_name': 'CapitalX'
        })
        
        return self.send_email(
            to_email=user.email,
            subject=subject,
            html_content=html_content
        )
    
    def send_referral_bonus(self, user, referral_user, bonus_amount):
        """Send referral bonus notification"""
        subject = f"CapitalX - Referral Bonus Earned (R{bonus_amount})"
        
        html_content = render_to_string('core/emails/referral_bonus.html', {
            'user': user,
            'referral_user': referral_user,
            'bonus_amount': bonus_amount,
            'site_name': 'CapitalX'
        })
        
        return self.send_email(
            to_email=user.email,
            subject=subject,
            html_content=html_content
        )
    
    def send_account_verification(self, user, verification_url):
        """Send account verification email"""
        subject = "CapitalX - Verify Your Account"
        
        html_content = render_to_string('core/emails/account_verification.html', {
            'user': user,
            'verification_url': verification_url,
            'site_name': 'CapitalX'
        })
        
        return self.send_email(
            to_email=user.email,
            subject=subject,
            html_content=html_content
        )
    
    def send_security_alert(self, user, alert_type, details):
        """Send security alert email"""
        subject = f"CapitalX - Security Alert: {alert_type}"
        
        html_content = render_to_string('core/emails/security_alert.html', {
            'user': user,
            'alert_type': alert_type,
            'details': details,
            'site_name': 'CapitalX'
        })
        
        return self.send_email(
            to_email=user.email,
            subject=subject,
            html_content=html_content
        )
    
    def send_otp_email(self, user, otp_code, purpose='email_verification', expiry_minutes=10):
        """Send OTP verification email"""
        purpose_titles = {
            'email_verification': 'Email Verification',
            'password_reset': 'Password Reset',
            'login_verification': 'Login Verification',
            'transaction_verification': 'Transaction Verification',
        }
        
        subject = f"CapitalX - {purpose_titles.get(purpose, 'Verification')} Code"
        
        html_content = render_to_string('core/emails/otp_verification.html', {
            'user': user,
            'otp_code': otp_code,
            'purpose': purpose_titles.get(purpose, 'Verification'),
            'expiry_minutes': expiry_minutes,
            'site_name': 'CapitalX'
        })
        
        return self.send_email(
            to_email=user.email,
            subject=subject,
            html_content=html_content
        )
    
    def send_custom_email(self, to_email, subject, template_name, context):
        """Send custom email using a specific template"""
        try:
            html_content = render_to_string(template_name, context)
            return self.send_email(
                to_email=to_email,
                subject=subject,
                html_content=html_content
            )
        except Exception as e:
            logger.error(f"Failed to send custom email: {str(e)}")
            return False

# Create a global instance
email_service = EmailService()

# Convenience functions for easy access
def send_welcome_email(user):
    """Send welcome email to new user"""
    return email_service.send_welcome_email(user)

def send_password_reset_email(user, reset_url):
    """Send password reset email"""
    return email_service.send_password_reset_email(user, reset_url)

def send_deposit_confirmation(user, deposit):
    """Send deposit confirmation email"""
    return email_service.send_deposit_confirmation(user, deposit)

def send_withdrawal_confirmation(user, withdrawal):
    """Send withdrawal confirmation email"""
    return email_service.send_withdrawal_confirmation(user, withdrawal)

def send_investment_update(user, investment):
    """Send investment update email"""
    return email_service.send_investment_update(user, investment)

def send_referral_bonus(user, referral_user, bonus_amount):
    """Send referral bonus notification"""
    return email_service.send_referral_bonus(user, referral_user, bonus_amount)

def send_account_verification(user, verification_url):
    """Send account verification email"""
    return email_service.send_account_verification(user, verification_url)

def send_security_alert(user, alert_type, details):
    """Send security alert email"""
    return email_service.send_security_alert(user, alert_type, details)

def send_otp_email(user, otp_code, purpose='email_verification', expiry_minutes=10):
    """Send OTP verification email"""
    return email_service.send_otp_email(user, otp_code, purpose, expiry_minutes)

def send_custom_email(to_email, subject, template_name, context):
    """Send custom email using a specific template"""
    return email_service.send_custom_email(to_email, subject, template_name, context)

def send_deposit_status_email(user, deposit, old_status, new_status):
    """Send deposit status change notification email"""
    from django.utils import timezone  # Import timezone here
    email_service = EmailService()
    
    if new_status == 'approved':
        subject = f"✅ Deposit Approved - R{deposit.amount}"
        template = 'core/emails/deposit_approved.html'
        
        # Email context
        context = {
            'user': user,
            'deposit': deposit,
            'amount': deposit.amount,
            'payment_method': deposit.get_payment_method_display(),
            'approved_date': timezone.now(),
            'site_url': 'http://localhost:8000',  # You can make this dynamic
        }
        
    elif new_status == 'rejected':
        subject = f"❌ Deposit Declined - R{deposit.amount}"
        template = 'core/emails/deposit_rejected.html'
        
        # Email context
        context = {
            'user': user,
            'deposit': deposit,
            'amount': deposit.amount,
            'payment_method': deposit.get_payment_method_display(),
            'rejected_date': timezone.now(),
            'admin_notes': deposit.admin_notes,
            'site_url': 'http://localhost:8000',
        }
        
    else:
        # For other status changes, send a generic update
        subject = f"📋 Deposit Status Update - R{deposit.amount}"
        template = 'core/emails/deposit_status_update.html'
        
        context = {
            'user': user,
            'deposit': deposit,
            'amount': deposit.amount,
            'old_status': old_status.title(),
            'new_status': new_status.title(),
            'payment_method': deposit.get_payment_method_display(),
            'updated_date': timezone.now(),
            'site_url': 'http://localhost:8000',
        }
    
    return email_service.send_email(
        to_email=user.email,
        subject=subject,
        template=template,
        context=context
    )

def send_referral_bonus_email(referrer, referred_user, reward_amount, deposit_amount):
    """Send email notification for referral bonus"""
    from django.utils import timezone
    
    subject = f"🎉 You Earned R{reward_amount} Referral Bonus!"
    template = 'core/emails/referral_bonus.html'
    
    context = {
        'referrer': referrer,
        'referred_user': referred_user,
        'reward_amount': reward_amount,
        'deposit_amount': deposit_amount,
        'earned_date': timezone.now(),
        'site_url': 'http://localhost:8000',
    }
    
    return send_custom_email(
        to_email=referrer.email,
        subject=subject,
        template_name=template,
        context=context
    )

def send_admin_deposit_notification(deposit):
    """Send email notification to admin when a user makes a deposit"""
    from django.utils import timezone
    
    admin_email = 'mkhabeleenterprise@gmail.com'
    subject = f"🏦 New Deposit Submitted - R{deposit.amount} from {deposit.user.username}"
    template = 'core/emails/admin_deposit_notification.html'
    
    context = {
        'deposit': deposit,
        'user': deposit.user,
        'amount': deposit.amount,
        'payment_method': deposit.get_payment_method_display(),
        'submitted_date': deposit.created_at,
        'admin_panel_url': 'http://localhost:8000/capitalx_admin/core/deposit/',
        'site_url': 'http://localhost:8000',
    }
    
    try:
        return send_custom_email(
            to_email=admin_email,
            subject=subject,
            template_name=template,
            context=context
        )
    except Exception as e:
        print(f"Failed to send admin deposit notification: {e}")
        return False
