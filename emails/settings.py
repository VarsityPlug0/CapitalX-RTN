"""
Configurable settings for the emails app.
All values can be overridden in Django's main settings.py file.
"""
import os
from django.conf import settings


def get_setting(name, default=None):
    """Get a setting value with fallback to default."""
    return getattr(settings, name, default)


# App Branding
EMAIL_APP_NAME = get_setting('EMAIL_APP_NAME', 'CapitalX')

# Site URL - used in email links
def get_site_url():
    """
    Get the production site URL for use in emails and templates.
    Priority: EMAIL_SITE_URL > RENDER_EXTERNAL_HOSTNAME > localhost
    """
    # Check for explicit site URL setting first
    site_url = get_setting('EMAIL_SITE_URL')
    if site_url:
        return site_url.rstrip('/')
    
    # Check for Render external hostname
    render_hostname = os.environ.get('RENDER_EXTERNAL_HOSTNAME')
    if render_hostname:
        return f'https://{render_hostname}'
    
    # Default to localhost for development
    return 'http://localhost:8000'


EMAIL_SITE_URL = get_site_url()

# Logo URL (optional - can be a full URL or relative path)
EMAIL_LOGO_URL = get_setting('EMAIL_LOGO_URL', '')

# Primary and secondary colors for email branding
EMAIL_PRIMARY_COLOR = get_setting('EMAIL_PRIMARY_COLOR', '#667eea')
EMAIL_SECONDARY_COLOR = get_setting('EMAIL_SECONDARY_COLOR', '#764ba2')

# Support and admin emails
EMAIL_SUPPORT_EMAIL = get_setting('EMAIL_SUPPORT_EMAIL', get_setting('DEFAULT_FROM_EMAIL', ''))
EMAIL_ADMIN_EMAIL = get_setting('EMAIL_ADMIN_EMAIL', get_setting('DEFAULT_FROM_EMAIL', ''))

# Footer settings
EMAIL_FOOTER_TEXT = get_setting('EMAIL_FOOTER_TEXT', f'© 2024 {EMAIL_APP_NAME}. All rights reserved.')
EMAIL_TAGLINE = get_setting('EMAIL_TAGLINE', 'Your Gateway to Smart Investments')
