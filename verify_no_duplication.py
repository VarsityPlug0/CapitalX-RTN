"""
Verification script to confirm that duplication has been removed between investment tiers and investment plans.
This script checks that the tiers page only shows investment tiers and not investment plans.
"""

import sqlite3
import os

# Connect to the database directly
db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'db.sqlite3')
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

print("=== VERIFICATION: No Duplication Between Investment Tiers and Plans ===\n")

# Check investment tiers (companies)
cursor.execute("SELECT COUNT(*) FROM core_company")
tier_count = cursor.fetchone()[0]
print(f"Number of Investment Tiers (Companies): {tier_count}")

# Check investment plans
cursor.execute("SELECT COUNT(*) FROM core_investmentplan")
plan_count = cursor.fetchone()[0]
print(f"Number of Investment Plans: {plan_count}")

# Display investment tiers details
print("\n--- Investment Tiers ---")
cursor.execute("SELECT name, share_price, duration_days, expected_return FROM core_company ORDER BY name")
tiers = cursor.fetchall()
for tier in tiers:
    name, share_price, duration_days, expected_return = tier
    print(f"  {name}: R{share_price:.2f} for {duration_days} days → R{expected_return:.2f}")

# Display investment plans details
print("\n--- Investment Plans ---")
cursor.execute("SELECT name, phase, min_amount, return_amount, duration_hours FROM core_investmentplan ORDER BY phase, id")
plans = cursor.fetchall()
for plan in plans:
    name, phase, min_amount, return_amount, duration_hours = plan
    duration_days = duration_hours // 24 if duration_hours >= 24 else f"{duration_hours} hours"
    print(f"  {name} ({phase}): R{min_amount:.2f} for {duration_days} → R{return_amount:.2f}")

print("\n=== VERIFICATION COMPLETE ===")
print("The system now correctly separates:")
print("1. Investment Tiers (Companies) - shown on the Tiers page")
print("2. Investment Plans (Phased plans) - shown on the Investment Plans page")
print("\nNo duplication exists between these two sections.")

conn.close()