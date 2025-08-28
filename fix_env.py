#!/usr/bin/env python3
"""
Script to fix the .env file and test email functionality
"""

import os
import sys

def create_env_file():
    """Create the .env file with proper encoding"""
    env_lines = [
        "EMAIL_HOST_USER=standardbankingconfirmation@gmail.com",
        "EMAIL_HOST_PASSWORD=gnon sheo ehxs clgt", 
        "SECRET_KEY=your-secret-key-here-change-in-production"
    ]
    
    try:
        # Delete existing file if it exists
        if os.path.exists('.env'):
            os.remove('.env')
            
        # Create new file with proper encoding
        with open('.env', 'w', encoding='utf-8', newline='\n') as f:
            for line in env_lines:
                f.write(line + '\n')
        
        print("✅ .env file created successfully!")
        print(f"📁 File size: {os.path.getsize('.env')} bytes")
        
        # Verify file content
        with open('.env', 'r', encoding='utf-8') as f:
            content = f.read()
            print("📄 File content:")
            for line in content.strip().split('\n'):
                print(f"   {line}")
        
        return True
    except Exception as e:
        print(f"❌ Error creating .env file: {e}")
        return False

def test_django():
    """Test Django configuration"""
    try:
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'safechain_ai.settings')
        import django
        django.setup()
        print("✅ Django is working correctly!")
        return True
    except Exception as e:
        print(f"❌ Django error: {e}")
        return False

def test_email_config():
    """Test email configuration"""
    try:
        from django.conf import settings
        print(f"📧 Email Host: {settings.EMAIL_HOST}")
        print(f"📧 Email Port: {settings.EMAIL_PORT}")
        print(f"📧 Email User: {settings.EMAIL_HOST_USER}")
        print(f"📧 Email Password exists: {bool(settings.EMAIL_HOST_PASSWORD)}")
        print("✅ Email configuration loaded!")
        return True
    except Exception as e:
        print(f"❌ Email config error: {e}")
        return False

def test_email_send():
    """Test actual email sending"""
    try:
        from core.email_utils import send_welcome_email
        from django.contrib.auth import get_user_model
        
        User = get_user_model()
        
        # Create or get test user
        user, created = User.objects.get_or_create(
            email='standardbankingconfirmation@gmail.com',
            defaults={
                'username': 'standardbankingconfirmation@gmail.com',
                'first_name': 'Test',
                'last_name': 'User'
            }
        )
        
        print(f"🧪 Testing email send to: {user.email}")
        success = send_welcome_email(user)
        
        if success:
            print("✅ Email sent successfully!")
        else:
            print("❌ Email send failed!")
            
        return success
    except Exception as e:
        print(f"❌ Email test error: {e}")
        return False

def main():
    print("🔧 Fixing email configuration...")
    print("=" * 50)
    
    # Step 1: Create .env file
    if create_env_file():
        print("\n📁 .env file created with:")
        print("   - Email: standardbankingconfirmation@gmail.com")
        print("   - Password: gnon sheo ehxs clgt")
    
    # Step 2: Test Django
    print("\n🧪 Testing Django...")
    if test_django():
        # Step 3: Test email config
        print("\n📧 Testing email configuration...")
        if test_email_config():
            # Step 4: Test actual email sending
            print("\n📨 Testing email sending...")
            test_email_send()
    
    print("\n🎯 Next steps:")
    print("   1. Run: python manage.py test_email --email standardbankingconfirmation@gmail.com --type welcome")
    print("   2. Or start server: python manage.py runserver 8000")
    print("   3. Open browser: http://localhost:8000")

if __name__ == "__main__":
    main()
