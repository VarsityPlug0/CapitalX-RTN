#!/usr/bin/env python3
"""
Script to create the .env file with proper email credentials
"""

import os

# Email credentials
env_content = """EMAIL_HOST_USER=standardbankingconfirmation@gmail.com
EMAIL_HOST_PASSWORD=tfzr brpz yuln ctwi
SECRET_KEY=your-secret-key-here-change-in-production
"""

# Create .env file
with open('.env', 'w', encoding='utf-8') as f:
    f.write(env_content)

print("✅ .env file created successfully!")
print("📧 Email:", "standardbankingconfirmation@gmail.com")
print("🔑 Password:", "tfzr brpz yuln ctwi"[:4] + "..." + "tfzr brpz yuln ctwi"[-4:])
print("\n📁 File location:", os.path.abspath('.env'))
