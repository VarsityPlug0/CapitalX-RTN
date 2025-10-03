# Script to fix the syntax error in views.py
import re

# Read the file
with open('core/views.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Find the problematic function
pattern = r'(@login_required\s+def user_financial_info_api\(request\):\s+)(\"\"\"[\s\S]*?\"\"\")(\s+try:)'

# Replace the docstring with a properly formatted one
replacement = r'\1"""API endpoint that returns user\'s financial information:\n    - Wallet balance\n    - Active investments\n    - Recent deposits\n    - Recent withdrawals\n    - Investment plans\n    """\3'

# Apply the fix
fixed_content = re.sub(pattern, replacement, content, count=1)

# Write the fixed content back to the file
with open('core/views.py', 'w', encoding='utf-8') as f:
    f.write(fixed_content)

print("Syntax error fixed!")