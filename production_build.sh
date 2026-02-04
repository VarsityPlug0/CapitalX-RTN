#!/usr/bin/env bash
# Production build script for Django on Render

# Exit on any error
set -e

echo "=== Starting Production Build ==="

# Update pip
echo "Updating pip..."
pip install --upgrade pip

# Install dependencies
echo "Installing Python dependencies..."
pip install -r requirements.txt

# Ensure static files directory exists
echo "Creating static files directory..."
mkdir -p staticfiles

# Collect static files with verbose output
echo "Collecting static files..."
python manage.py collectstatic --noinput --verbosity=2

# Run database migrations
echo "Running database migrations..."
python manage.py migrate

# Create initial data (if needed)
echo "Creating investment tiers..."
python manage.py create_investment_tiers

echo "Creating investment plans..."
python manage.py create_investment_plans

# Create superuser if it doesn't exist
echo "Setting up admin user..."
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
            
    print("Build script completed successfully!")
    
except Exception as e:
    print(f"ERROR in build script: {e}")
    import traceback
    traceback.print_exc()
    exit(1)
EOF

echo "=== Build completed successfully! ==="