import sqlite3
import os

# Connect to the database directly
db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'db.sqlite3')
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Query the investment tiers
cursor.execute("SELECT name, share_price, duration_days, expected_return FROM core_company ORDER BY name")
tiers = cursor.fetchall()

print("Current Investment Tiers:")
print("=" * 50)
for tier in tiers:
    name, share_price, duration_days, expected_return = tier
    print(f"{name}")
    print(f"  Investment: R{share_price:.2f}")
    print(f"  Duration: {duration_days} days")
    print(f"  Expected Return: R{expected_return:.2f}")
    print()

conn.close()