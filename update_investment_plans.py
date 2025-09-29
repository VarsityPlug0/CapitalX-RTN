import os
import django
from decimal import Decimal

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'safechain_ai.settings')
django.setup()

from core.models import InvestmentPlan

def update_investment_plans():
    # Define the investment plans as shown in the content
    plans = [
        # Phase 1 (Short-Term)
        {
            'name': 'Shoprite Plan',
            'phase': 'phase_1',
            'emoji': '🛒',
            'min_amount': Decimal('60.00'),
            'max_amount': Decimal('60.00'),
            'return_amount': Decimal('100.00'),
            'duration_hours': 12,
            'phase_order': 1,
            'plan_order': 1,
            'description': 'Quick return investment with Shoprite partnership. Perfect for beginners looking for fast returns.'
        },
        {
            'name': 'Mr Price Plan',
            'phase': 'phase_1',
            'emoji': '👕',
            'min_amount': Decimal('100.00'),
            'max_amount': Decimal('100.00'),
            'return_amount': Decimal('200.00'),
            'duration_hours': 24,
            'phase_order': 1,
            'plan_order': 2,
            'description': 'Fashion retail investment opportunity with guaranteed 100% returns in 24 hours.'
        },
        {
            'name': 'Capitec Plan',
            'phase': 'phase_1',
            'emoji': '🏦',
            'min_amount': Decimal('500.00'),
            'max_amount': Decimal('500.00'),
            'return_amount': Decimal('1500.00'),
            'duration_hours': 72,
            'phase_order': 1,
            'plan_order': 3,
            'description': 'Banking sector investment with Capitec partnership. Triple your investment in just 3 days.'
        },
        
        # Phase 2 (Mid-Term)
        {
            'name': 'MTN Plan',
            'phase': 'phase_2',
            'emoji': '📱',
            'min_amount': Decimal('1000.00'),
            'max_amount': Decimal('1000.00'),
            'return_amount': Decimal('4000.00'),
            'duration_hours': 168,
            'phase_order': 2,
            'plan_order': 1,
            'description': 'Telecommunications investment with MTN. 4x returns in one week through 5G infrastructure growth.'
        },
        {
            'name': 'Vodacom Plan',
            'phase': 'phase_2',
            'emoji': '📡',
            'min_amount': Decimal('2000.00'),
            'max_amount': Decimal('2000.00'),
            'return_amount': Decimal('8000.00'),
            'duration_hours': 336,
            'phase_order': 2,
            'plan_order': 2,
            'description': 'Premium telecom investment with Vodacom. 4x returns leveraging network expansion.'
        },
        {
            'name': 'Discovery Plan',
            'phase': 'phase_2',
            'emoji': '🏥',
            'min_amount': Decimal('3000.00'),
            'max_amount': Decimal('3000.00'),
            'return_amount': Decimal('12000.00'),
            'duration_hours': 504,
            'phase_order': 2,
            'plan_order': 3,
            'description': 'Healthcare and insurance investment with Discovery. 4x returns through medical innovation.'
        },
        
        # Phase 3 (Long-Term)
        {
            'name': 'Sasol Plan',
            'phase': 'phase_3',
            'emoji': '⛽',
            'min_amount': Decimal('4000.00'),
            'max_amount': Decimal('4000.00'),
            'return_amount': Decimal('15000.00'),
            'duration_hours': 720,
            'phase_order': 3,
            'plan_order': 1,
            'description': 'Energy sector investment with Sasol. High returns through oil and gas operations.'
        },
        {
            'name': 'Standard Bank Plan',
            'phase': 'phase_3',
            'emoji': '🏛️',
            'min_amount': Decimal('5000.00'),
            'max_amount': Decimal('5000.00'),
            'return_amount': Decimal('20000.00'),
            'duration_hours': 720,
            'phase_order': 3,
            'plan_order': 2,
            'description': 'Premium banking investment with Standard Bank. 4x returns through institutional banking.'
        },
        {
            'name': 'Naspers Plan',
            'phase': 'phase_3',
            'emoji': '💼',
            'min_amount': Decimal('10000.00'),
            'max_amount': Decimal('10000.00'),
            'return_amount': Decimal('50000.00'),
            'duration_hours': 1440,
            'phase_order': 3,
            'plan_order': 3,
            'description': 'Premium media and tech conglomerate investment. 5x returns through tech innovation.'
        }
    ]

    # Update or create the investment plans
    for plan_data in plans:
        plan, created = InvestmentPlan.objects.update_or_create(
            name=plan_data['name'],
            phase=plan_data['phase'],
            defaults=plan_data
        )
        if created:
            print(f"Created new plan: {plan_data['name']}")
        else:
            print(f"Updated existing plan: {plan_data['name']}")

if __name__ == '__main__':
    print("Updating investment plans to match content...")
    update_investment_plans()
    print("Investment plans updated successfully!")