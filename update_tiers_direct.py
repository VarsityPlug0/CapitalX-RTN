import sqlite3
import os
from decimal import Decimal

# Connect to the database directly
db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'db.sqlite3')
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Define the new tiers as shown in the content
new_tiers = [
    {
        'name': 'Foundation Tier',
        'share_price': 50.00,
        'expected_return': 1120.00,
        'duration_days': 7,
        'min_level': 1,
        'description': 'Perfect for beginners. Start your investment journey with our Foundation Tier.'
    },
    {
        'name': 'Growth Tier',
        'share_price': 500.00,
        'expected_return': 17920.00,
        'duration_days': 14,
        'min_level': 1,
        'description': 'For growing investors. Higher returns with our Growth Tier investment plan.'
    },
    {
        'name': 'Premium Tier',
        'share_price': 2000.00,
        'expected_return': 50000.00,
        'duration_days': 30,
        'min_level': 1,
        'description': 'Maximum returns for serious investors. Premium opportunities with our top tier.'
    }
]

# Update or create the new tiers
for tier in new_tiers:
    # Check if the tier already exists
    cursor.execute("SELECT id FROM core_company WHERE name = ?", (tier['name'],))
    result = cursor.fetchone()
    
    if result:
        # Update existing tier
        cursor.execute("""
            UPDATE core_company 
            SET share_price = ?, expected_return = ?, duration_days = ?, min_level = ?, description = ?
            WHERE name = ?
        """, (
            tier['share_price'],
            tier['expected_return'],
            tier['duration_days'],
            tier['min_level'],
            tier['description'],
            tier['name']
        ))
        print(f"Updated existing tier: {tier['name']}")
    else:
        # Create new tier
        cursor.execute("""
            INSERT INTO core_company (name, share_price, expected_return, duration_days, min_level, description, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, datetime('now'), datetime('now'))
        """, (
            tier['name'],
            tier['share_price'],
            tier['expected_return'],
            tier['duration_days'],
            tier['min_level'],
            tier['description']
        ))
        print(f"Created new tier: {tier['name']}")

# Commit changes and close connection
conn.commit()
conn.close()

print("Investment tiers updated successfully!")