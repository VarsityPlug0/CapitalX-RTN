import os
import django

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'safechain_ai.settings')
django.setup()

from core.models import Company, InvestmentPlan

print("Checking Companies:")
companies = Company.objects.all()
for company in companies:
    print(f"  {company.name} - R{company.share_price}")

print("\nChecking Investment Plans:")
plans = InvestmentPlan.objects.all().order_by('phase_order', 'plan_order')
for plan in plans:
    print(f"  {plan.emoji} {plan.name} - R{plan.min_amount} -> R{plan.return_amount} ({plan.get_duration_display()})")