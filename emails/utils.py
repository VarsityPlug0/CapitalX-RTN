"""
Utility functions for the emails app.
"""
from . import settings as email_settings


def get_site_url():
    """
    Get the production site URL for use in emails and templates.
    This ensures all email links point to the correct domain.
    """
    return email_settings.get_site_url()


def get_email_context(extra_context=None):
    """
    Get common context variables for email templates.
    Includes all branding and configuration values.
    
    Args:
        extra_context: Optional dict of additional context to merge
        
    Returns:
        dict: Context with all email branding variables
    """
    context = {
        'app_name': email_settings.EMAIL_APP_NAME,
        'site_name': email_settings.EMAIL_APP_NAME,  # Alias for compatibility
        'site_url': get_site_url(),
        'logo_url': email_settings.EMAIL_LOGO_URL,
        'primary_color': email_settings.EMAIL_PRIMARY_COLOR,
        'secondary_color': email_settings.EMAIL_SECONDARY_COLOR,
        'support_email': email_settings.EMAIL_SUPPORT_EMAIL,
        'admin_email': email_settings.EMAIL_ADMIN_EMAIL,
        'footer_text': email_settings.EMAIL_FOOTER_TEXT,
        'tagline': email_settings.EMAIL_TAGLINE,
    }
    
    if extra_context:
        context.update(extra_context)
    
    return context
