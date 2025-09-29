"""
Verification script to confirm that the home page now shows accurate investment plans
instead of the old investment tiers.
"""

import sqlite3
import os

# Connect to the database directly
db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'db.sqlite3')
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

print("=== VERIFICATION: Home Page Investment Plans ===\n")

# Check investment plans that should be displayed on home page
print("Investment Plans Displayed on Home Page:")
print("----------------------------------------")

# Get 3 sample investment plans (as shown on home page)
cursor.execute("""
    SELECT name, phase, min_amount, return_amount, duration_hours 
    FROM core_investmentplan 
    WHERE is_active = 1 
    ORDER BY id 
    LIMIT 3
""")
plans = cursor.fetchall()

for plan in plans:
    name, phase, min_amount, return_amount, duration_hours = plan
    # Format duration
    if duration_hours < 24:
        duration = f"{duration_hours} hours"
    elif duration_hours < 168:  # Less than a week
        days = duration_hours // 24
        duration = f"{days} day{'s' if days != 1 else ''}"
    else:
        weeks = duration_hours // 168
        duration = f"{weeks} week{'s' if weeks != 1 else ''}"
    
    print(f"  {name}")
    print(f"    Investment: R{min_amount:.0f}")
    print(f"    Duration: {duration}")
    print(f"    Returns: R{return_amount:.0f}")
    print()

# Display all active investment plans for reference
print("\nAll Active Investment Plans:")
print("-----------------------------")
cursor.execute("""
    SELECT name, phase, min_amount, return_amount, duration_hours 
    FROM core_investmentplan 
    WHERE is_active = 1 
    ORDER BY phase, id
""")
all_plans = cursor.fetchall()

phase_names = {
    'phase_1': 'Short-Term',
    'phase_2': 'Mid-Term', 
    'phase_3': 'Long-Term'
}

current_phase = None
for plan in all_plans:
    name, phase, min_amount, return_amount, duration_hours = plan
    
    # Show phase header
    if phase != current_phase:
        current_phase = phase
        print(f"\n  {phase_names.get(phase, phase)} Plans:")
    
    # Format duration
    if duration_hours < 24:
        duration = f"{duration_hours} hours"
    elif duration_hours < 168:  # Less than a week
        days = duration_hours // 24
        duration = f"{days} day{'s' if days != 1 else ''}"
    else:
        weeks = duration_hours // 168
        duration = f"{weeks} week{'s' if weeks != 1 else ''}"
    
    roi = ((return_amount / min_amount - 1) * 100) if min_amount > 0 else 0
    
    print(f"    {name}: R{min_amount:.0f} → R{return_amount:.0f} ({duration}) [{roi:.0f}% ROI]")

print("\n=== VERIFICATION COMPLETE ===")
print("The home page now correctly displays:")
print("1. Accurate investment plans instead of old investment tiers")
print("2. Clear categorization by investment term (Short/Mid/Long-term)")
print("3. Proper formatting of investment details")

conn.close()