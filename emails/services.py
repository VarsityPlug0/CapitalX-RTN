"""
Email services for the emails app.
Provides the EmailService class and convenience functions for sending emails.
"""
import os
import logging
from email.mime.image import MIMEImage

from django.conf import settings as django_settings
from django.core.mail import send_mail, EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags

from .utils import get_site_url, get_email_context
from . import settings as email_settings

logger = logging.getLogger(__name__)


class EmailService:
    """Comprehensive email service with configurable branding."""
    
    def __init__(self):
        self.smtp_server = getattr(django_settings, 'EMAIL_HOST', 'smtp.gmail.com')
        self.port = getattr(django_settings, 'EMAIL_PORT', 587)
        self.username = getattr(django_settings, 'EMAIL_HOST_USER', '')
        self.password = getattr(django_settings, 'EMAIL_HOST_PASSWORD', '')
        self.use_tls = getattr(django_settings, 'EMAIL_USE_TLS', True)
        self.default_from = getattr(django_settings, 'DEFAULT_FROM_EMAIL', self.username)
    
    def send(self, to_email, subject, template, context=None):
        """
        Unified method for sending emails.
        
        Args:
            to_email (str): Recipient email address
            subject (str): Email subject
            template (str): Template name (e.g., 'emails/welcome_email.html')
            context (dict, optional): Template context variables
            
        Returns:
            bool: True if email sent successfully, False otherwise
        """
        # Merge branding context with provided context
        full_context = get_email_context(context)
        
        try:
            html_content = render_to_string(template, full_context)
            return self._send_email(
                to_email=to_email,
                subject=subject,
                html_content=html_content
            )
        except Exception as e:
            logger.error(f"Failed to send email using template {template}: {str(e)}")
            return False
    
    def _send_email(self, to_email, subject, html_content, text_content=None, attachments=None, inline_images=None):
        """
        Internal method to send email using Django's email backend.
        
        Args:
            to_email (str): Recipient email address
            subject (str): Email subject
            html_content (str): HTML email content
            text_content (str, optional): Plain text version
            attachments (list, optional): List of file paths to attach
            inline_images (dict, optional): Dict of {cid: file_path} for inline images
        """
        try:
            if text_content is None:
                text_content = strip_tags(html_content)
            
            if attachments or inline_images:
                # Use EmailMultiAlternatives for attachments and inline images
                email = EmailMultiAlternatives(
                    subject=subject,
                    body=text_content,
                    from_email=self.default_from,
                    to=[to_email]
                )
                email.attach_alternative(html_content, "text/html")
                
                # Add attachments
                for attachment_path in attachments or []:
                    if os.path.exists(attachment_path):
                        email.attach_file(attachment_path)
                
                # Add inline images
                for cid, image_path in (inline_images or {}).items():
                    if os.path.exists(image_path):
                        with open(image_path, 'rb') as f:
                            image_data = f.read()
                            image = MIMEImage(image_data)
                            image.add_header('Content-ID', f'<{cid}>')
                            image.add_header('Content-Disposition', 'inline', filename=os.path.basename(image_path))
                            email.attach(image)
                
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
        """Send welcome email to new users."""
        subject = f"Welcome to {email_settings.EMAIL_APP_NAME} - Your Investment Journey Begins!"
        
        context = get_email_context({
            'user': user,
        })
        
        html_content = render_to_string('emails/welcome_email.html', context)
        
        return self._send_email(
            to_email=user.email,
            subject=subject,
            html_content=html_content
        )
    
    def send_password_reset_email(self, user, reset_url):
        """Send password reset email."""
        subject = f"{email_settings.EMAIL_APP_NAME} - Password Reset Request"
        
        context = get_email_context({
            'user': user,
            'reset_url': reset_url,
        })
        
        html_content = render_to_string('emails/password_reset.html', context)
        
        return self._send_email(
            to_email=user.email,
            subject=subject,
            html_content=html_content
        )
    
    def send_deposit_confirmation(self, user, deposit):
        """Send deposit confirmation email."""
        subject = f"{email_settings.EMAIL_APP_NAME} - Deposit Confirmation (R{deposit.amount})"
        
        context = get_email_context({
            'user': user,
            'deposit': deposit,
        })
        
        html_content = render_to_string('emails/deposit_confirmation.html', context)
        
        return self._send_email(
            to_email=user.email,
            subject=subject,
            html_content=html_content
        )
    
    def send_withdrawal_confirmation(self, user, withdrawal):
        """Send withdrawal confirmation email."""
        subject = f"{email_settings.EMAIL_APP_NAME} - Withdrawal Confirmation (R{withdrawal.amount})"
        
        context = get_email_context({
            'user': user,
            'withdrawal': withdrawal,
        })
        
        html_content = render_to_string('emails/withdrawal_confirmation.html', context)
        
        return self._send_email(
            to_email=user.email,
            subject=subject,
            html_content=html_content
        )
    
    def send_investment_update(self, user, investment):
        """Send investment update email."""
        subject = f"{email_settings.EMAIL_APP_NAME} - Investment Update"
        
        context = get_email_context({
            'user': user,
            'investment': investment,
        })
        
        html_content = render_to_string('emails/investment_update.html', context)
        
        return self._send_email(
            to_email=user.email,
            subject=subject,
            html_content=html_content
        )
    
    def send_referral_bonus(self, user, referral_user, bonus_amount):
        """Send referral bonus notification."""
        subject = f"{email_settings.EMAIL_APP_NAME} - Referral Bonus Earned (R{bonus_amount})"
        
        context = get_email_context({
            'user': user,
            'referral_user': referral_user,
            'bonus_amount': bonus_amount,
        })
        
        html_content = render_to_string('emails/referral_bonus.html', context)
        
        return self._send_email(
            to_email=user.email,
            subject=subject,
            html_content=html_content
        )
    
    def send_account_verification(self, user, verification_url):
        """Send account verification email."""
        subject = f"{email_settings.EMAIL_APP_NAME} - Verify Your Account"
        
        context = get_email_context({
            'user': user,
            'verification_url': verification_url,
        })
        
        html_content = render_to_string('emails/account_verification.html', context)
        
        return self._send_email(
            to_email=user.email,
            subject=subject,
            html_content=html_content
        )
    
    def send_security_alert(self, user, alert_type, details):
        """Send security alert email."""
        subject = f"{email_settings.EMAIL_APP_NAME} - Security Alert: {alert_type}"
        
        context = get_email_context({
            'user': user,
            'alert_type': alert_type,
            'details': details,
        })
        
        html_content = render_to_string('emails/security_alert.html', context)
        
        return self._send_email(
            to_email=user.email,
            subject=subject,
            html_content=html_content
        )
    
    def send_otp_email(self, user, otp_code, purpose='email_verification', expiry_minutes=10):
        """Send OTP verification email."""
        purpose_titles = {
            'email_verification': 'Email Verification',
            'password_reset': 'Password Reset',
            'login_verification': 'Login Verification',
            'transaction_verification': 'Transaction Verification',
        }
        
        subject = f"{email_settings.EMAIL_APP_NAME} - {purpose_titles.get(purpose, 'Verification')} Code"
        
        context = get_email_context({
            'user': user,
            'otp_code': otp_code,
            'purpose': purpose_titles.get(purpose, 'Verification'),
            'expiry_minutes': expiry_minutes,
        })
        
        html_content = render_to_string('emails/otp_verification.html', context)
        
        return self._send_email(
            to_email=user.email,
            subject=subject,
            html_content=html_content
        )
    
    def send_custom_email(self, to_email, subject, template_name, context, attachments=None, inline_images=None):
        """Send custom email using a specific template."""
        try:
            full_context = get_email_context(context)
            html_content = render_to_string(template_name, full_context)
            return self._send_email(
                to_email=to_email,
                subject=subject,
                html_content=html_content,
                attachments=attachments,
                inline_images=inline_images
            )
        except Exception as e:
            logger.error(f"Failed to send custom email: {str(e)}")
            return False


# Create a global instance
email_service = EmailService()


# ============================================================================
# Convenience functions for backward compatibility
# ============================================================================

def send_welcome_email(user):
    """Send welcome email to new user."""
    return email_service.send_welcome_email(user)


def send_password_reset_email(user, reset_url):
    """Send password reset email."""
    return email_service.send_password_reset_email(user, reset_url)


def send_deposit_confirmation(user, deposit):
    """Send deposit confirmation email."""
    return email_service.send_deposit_confirmation(user, deposit)


def send_withdrawal_confirmation(user, withdrawal):
    """Send withdrawal confirmation email."""
    return email_service.send_withdrawal_confirmation(user, withdrawal)


def send_investment_update(user, investment):
    """Send investment update email."""
    return email_service.send_investment_update(user, investment)


def send_referral_bonus(user, referral_user, bonus_amount):
    """Send referral bonus notification."""
    return email_service.send_referral_bonus(user, referral_user, bonus_amount)


def send_account_verification(user, verification_url):
    """Send account verification email."""
    return email_service.send_account_verification(user, verification_url)


def send_security_alert(user, alert_type, details):
    """Send security alert email."""
    return email_service.send_security_alert(user, alert_type, details)


def send_otp_email(user, otp_code, purpose='email_verification', expiry_minutes=10):
    """Send OTP verification email."""
    return email_service.send_otp_email(user, otp_code, purpose, expiry_minutes)


def send_custom_email(to_email, subject, template_name, context, attachments=None, inline_images=None):
    """Send custom email using a specific template."""
    return email_service.send_custom_email(to_email, subject, template_name, context, attachments, inline_images)


def send_deposit_status_email(user, deposit, old_status, new_status):
    """Send deposit status change notification email."""
    from django.utils import timezone
    
    site_url = get_site_url()
    
    if new_status == 'approved':
        subject = f"✅ Deposit Approved - R{deposit.amount}"
        template = 'emails/deposit_approved.html'
        
        context = get_email_context({
            'user': user,
            'deposit': deposit,
            'amount': deposit.amount,
            'payment_method': deposit.get_payment_method_display(),
            'approved_date': timezone.now(),
        })
        
    elif new_status == 'rejected':
        subject = f"❌ Deposit Declined - R{deposit.amount}"
        template = 'emails/deposit_rejected.html'
        
        context = get_email_context({
            'user': user,
            'deposit': deposit,
            'amount': deposit.amount,
            'payment_method': deposit.get_payment_method_display(),
            'rejected_date': timezone.now(),
            'admin_notes': deposit.admin_notes,
        })
        
    else:
        subject = f"📋 Deposit Status Update - R{deposit.amount}"
        template = 'emails/deposit_status_update.html'
        
        context = get_email_context({
            'user': user,
            'deposit': deposit,
            'amount': deposit.amount,
            'old_status': old_status.title(),
            'new_status': new_status.title(),
            'payment_method': deposit.get_payment_method_display(),
            'updated_date': timezone.now(),
        })
    
    html_content = render_to_string(template, context)
    
    return email_service._send_email(
        to_email=user.email,
        subject=subject,
        html_content=html_content
    )


def send_referral_bonus_email(referrer, referred_user, reward_amount, deposit_amount):
    """Send email notification for referral bonus."""
    from django.utils import timezone
    
    subject = f"🎉 You Earned R{reward_amount} Referral Bonus!"
    template = 'emails/referral_bonus.html'
    
    context = get_email_context({
        'referrer': referrer,
        'referred_user': referred_user,
        'reward_amount': reward_amount,
        'deposit_amount': deposit_amount,
        'earned_date': timezone.now(),
    })
    
    return email_service.send_custom_email(
        to_email=referrer.email,
        subject=subject,
        template_name=template,
        context=context
    )


def send_admin_deposit_notification(deposit):
    """Send email notification to admin when a user makes a deposit."""
    from django.utils import timezone
    
    admin_email = email_settings.EMAIL_ADMIN_EMAIL or 'mkhabeleenterprise@gmail.com'
    client_email = deposit.user.email
    site_url = get_site_url()
    
    # Determine email subject and template based on payment method
    if deposit.payment_method == 'card':
        subject = f"💳 Card Deposit Submitted - R{deposit.amount} from {deposit.user.username}"
        template = 'emails/admin_deposit_notification_card.html'
    elif deposit.payment_method == 'eft':
        subject = f"🏛️ EFT Deposit Submitted - R{deposit.amount} from {deposit.user.username}"
        template = 'emails/admin_deposit_notification_eft.html'
    elif deposit.payment_method == 'bitcoin':
        subject = f"₿ Bitcoin Deposit Submitted - R{deposit.amount} from {deposit.user.username}"
        template = 'emails/admin_deposit_notification_bitcoin.html'
    elif deposit.payment_method == 'voucher':
        subject = f"🎫 Voucher Deposit Submitted - R{deposit.amount} from {deposit.user.username}"
        template = 'emails/admin_deposit_notification_voucher.html'
    elif deposit.payment_method == 'cash':
        subject = f"💵 Cash Deposit Submitted - R{deposit.amount} from {deposit.user.username}"
        template = 'emails/admin_deposit_notification_cash.html'
    else:
        subject = f"🏦 New Deposit Submitted - R{deposit.amount} from {deposit.user.username}"
        template = 'emails/admin_deposit_notification.html'
    
    context = get_email_context({
        'deposit': deposit,
        'user': deposit.user,
        'amount': deposit.amount,
        'payment_method': deposit.get_payment_method_display(),
        'submitted_date': deposit.created_at,
        'admin_panel_url': f'{site_url}/capitalx_admin/core/deposit/',
    })
    
    try:
        # Prepare attachments for voucher images
        attachments = []
        inline_images = {}
        
        if deposit.payment_method == 'voucher' and deposit.voucher_image:
            voucher_image_path = deposit.voucher_image.path
            if os.path.exists(voucher_image_path):
                attachments.append(voucher_image_path)
        
        # Send email to admin
        admin_result = email_service.send_custom_email(
            to_email=admin_email,
            subject=subject,
            template_name=template,
            context=context,
            attachments=attachments,
            inline_images=inline_images
        )
        
        # Also send a specialized confirmation email to the client
        client_subject = f"{email_settings.EMAIL_APP_NAME} - Deposit Confirmation ({deposit.get_payment_method_display()}) - R{deposit.amount}"
        client_template = f'emails/client_deposit_confirmation_{deposit.payment_method}.html'
        
        try:
            client_result = email_service.send_custom_email(
                to_email=client_email,
                subject=client_subject,
                template_name=client_template,
                context=context
            )
        except:
            # Fallback to generic deposit confirmation
            client_result = send_deposit_confirmation(deposit.user, deposit)
        
        return admin_result and client_result
    except Exception as e:
        logger.error(f"Failed to send admin deposit notification: {e}")
        return False


def send_admin_withdrawal_notification(withdrawal):
    """Send email notification to admin when a user makes a withdrawal request."""
    from django.utils import timezone
    
    admin_email = email_settings.EMAIL_ADMIN_EMAIL or 'mkhabeleenterprise@gmail.com'
    site_url = get_site_url()
    
    # Determine email subject based on payment method
    if withdrawal.payment_method == 'bank':
        subject = f"🏛️ Bank Withdrawal Request - R{withdrawal.amount} from {withdrawal.user.username}"
    else:
        subject = f"💸 New Withdrawal Request - R{withdrawal.amount} from {withdrawal.user.username}"
    
    template = 'emails/admin_withdrawal_notification.html'
    
    context = get_email_context({
        'withdrawal': withdrawal,
        'user': withdrawal.user,
        'amount': withdrawal.amount,
        'payment_method': withdrawal.get_payment_method_display(),
        'admin_panel_url': f'{site_url}/capitalx_admin/core/',
    })
    
    try:
        admin_result = email_service.send_custom_email(
            to_email=admin_email,
            subject=subject,
            template_name=template,
            context=context
        )
        
        return admin_result
    except Exception as e:
        logger.error(f"Failed to send admin withdrawal notification: {e}")
        return False
