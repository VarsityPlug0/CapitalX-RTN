#!/usr/bin/env bash
# exit on error
set -o errexit

# Install Python dependencies
pip install -r requirements.txt

# Collect static files
python manage.py collectstatic --no-input

# Apply database migrations
python manage.py migrate

# Create superuser if it doesn't exist
python manage.py shell << EOF
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
EOF

echo "Build completed successfully!"
