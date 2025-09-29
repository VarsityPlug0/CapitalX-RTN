#!/usr/bin/env bash
# exit on error
set -o errexit

# Update pip first
pip install --upgrade pip

# Install Python dependencies with verbose output
pip install -r requirements.txt --verbose

# Collect static files
python manage.py collectstatic --no-input

# Apply database migrations
python manage.py migrate

# Create investment tiers
python manage.py create_investment_tiers

# Create investment plans
python manage.py create_investment_plans

# Create superuser if it doesn't exist (with error handling)
python manage.py shell << 'EOF'
try:
    from django.contrib.auth import get_user_model
    from core.models import Wallet
    import os

    User = get_user_model()
    admin_email = 'mukoni@gmail.com'
    admin_password = 'admin123'

    if not User.objects.filter(email=admin_email).exists():
        print(f"Creating admin user: {admin_email}")
        admin_user = User.objects.create_superuser(
            username=admin_email,
            email=admin_email,
            password=admin_password,
            first_name='Admin',
            last_name='User',
            is_email_verified=True
        )
        print(f"Admin user created successfully!")
        
        # Create wallet for admin
        wallet, created = Wallet.objects.get_or_create(user=admin_user)
        if created:
            print("Admin wallet created!")
    else:
        print(f"Admin user {admin_email} already exists")
        # Ensure admin has correct privileges
        admin_user = User.objects.get(email=admin_email)
        if not admin_user.is_staff:
            admin_user.is_staff = True
            admin_user.save()
            print("Updated admin user to staff status")
        if not admin_user.is_superuser:
            admin_user.is_superuser = True
            admin_user.save()
            print("Updated admin user to superuser status")
            
    # Test imports to catch issues early
    print("Testing imports...")
    import reportlab
    print(f"ReportLab version: {reportlab.Version}")
    import dns
    print("DNS library available")
    
    # Test lead system imports
    from core.lead_system import EmailLeadSystem
    from core.lead_generator import AutomatedLeadGenerator
    print("Lead system imports successful")
    
    print("Build script completed successfully!")
    
except Exception as e:
    print(f"ERROR in build script: {e}")
    import traceback
    traceback.print_exc()
    exit(1)
EOF

echo "Build completed successfully!"