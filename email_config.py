"""
Email Configuration for CapitalX

This file contains the email configuration settings for the CapitalX application.
To use email functionality, you need to set up your email credentials.

1. Create a .env file in your project root
2. Add your email credentials to the .env file
3. Update the settings below if needed

Example .env file:
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
"""

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Email Configuration
EMAIL_CONFIG = {
    'EMAIL_BACKEND': 'django.core.mail.backends.smtp.EmailBackend',
    'EMAIL_HOST': 'smtp.gmail.com',  # Gmail SMTP server
    'EMAIL_PORT': 587,               # TLS port
    'EMAIL_USE_TLS': True,           # Use TLS encryption
    'EMAIL_HOST_USER': os.getenv('EMAIL_HOST_USER', ''),           # Your email
    'EMAIL_HOST_PASSWORD': os.getenv('EMAIL_HOST_PASSWORD', ''),   # Your app password
    'DEFAULT_FROM_EMAIL': os.getenv('EMAIL_HOST_USER', ''),       # Default sender
}

# Alternative email providers
EMAIL_PROVIDERS = {
    'gmail': {
        'EMAIL_HOST': 'smtp.gmail.com',
        'EMAIL_PORT': 587,
        'EMAIL_USE_TLS': True,
    },
    'outlook': {
        'EMAIL_HOST': 'smtp-mail.outlook.com',
        'EMAIL_PORT': 587,
        'EMAIL_USE_TLS': True,
    },
    'yahoo': {
        'EMAIL_HOST': 'smtp.mail.yahoo.com',
        'EMAIL_PORT': 587,
        'EMAIL_USE_TLS': True,
    },
    'sendgrid': {
        'EMAIL_HOST': 'smtp.sendgrid.net',
        'EMAIL_PORT': 587,
        'EMAIL_USE_TLS': True,
    }
}

def get_email_config(provider='gmail'):
    """
    Get email configuration for a specific provider
    
    Args:
        provider (str): Email provider name (gmail, outlook, yahoo, sendgrid)
    
    Returns:
        dict: Email configuration dictionary
    """
    if provider not in EMAIL_PROVIDERS:
        provider = 'gmail'
    
    config = EMAIL_CONFIG.copy()
    config.update(EMAIL_PROVIDERS[provider])
    
    return config

def test_email_connection():
    """
    Test email connection with current settings
    
    Returns:
        bool: True if connection successful, False otherwise
    """
    try:
        import smtplib
        
        # Get current email config
        config = get_email_config()
        
        # Test connection
        server = smtplib.SMTP(config['EMAIL_HOST'], config['EMAIL_PORT'])
        server.starttls()
        server.login(config['EMAIL_HOST_USER'], config['EMAIL_HOST_PASSWORD'])
        server.quit()
        
        print("✅ Email connection test successful!")
        return True
        
    except Exception as e:
        print(f"❌ Email connection test failed: {e}")
        return False

def print_email_setup_instructions():
    """
    Print instructions for setting up email functionality
    """
    print("\n" + "="*60)
    print("📧 EMAIL SETUP INSTRUCTIONS FOR CAPITALX")
    print("="*60)
    
    print("\n1. 📝 Create a .env file in your project root")
    print("2. 🔑 Add your email credentials:")
    print("   EMAIL_HOST_USER=your-email@gmail.com")
    print("   EMAIL_HOST_PASSWORD=your-app-password")
    
    print("\n3. 🔐 For Gmail, you need an App Password:")
    print("   - Go to Google Account settings")
    print("   - Enable 2-Factor Authentication")
    print("   - Generate an App Password")
    print("   - Use the App Password in EMAIL_HOST_PASSWORD")
    
    print("\n4. 🧪 Test your email setup:")
    print("   python manage.py test_email --email your-email@example.com")
    
    print("\n5. 🌐 Supported email providers:")
    for provider in EMAIL_PROVIDERS.keys():
        print(f"   - {provider.capitalize()}")
    
    print("\n6. ⚠️  Important:")
    print("   - Never commit your .env file to version control")
    print("   - Use App Passwords for Gmail (not your regular password)")
    print("   - Test emails in development before production")
    
    print("\n" + "="*60)

if __name__ == "__main__":
    print_email_setup_instructions()
    
    # Check if email credentials are set
    if EMAIL_CONFIG['EMAIL_HOST_USER'] and EMAIL_CONFIG['EMAIL_HOST_PASSWORD']:
        print("\n🔍 Testing email connection...")
        test_email_connection()
    else:
        print("\n❌ Email credentials not found in .env file")
        print("Please follow the setup instructions above.")
