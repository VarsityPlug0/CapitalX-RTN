from django.core.management.base import BaseCommand
from core.models import Company, InvestmentPlan

class Command(BaseCommand):
    help = 'Verify investment data in the database'

    def handle(self, *args, **options):
        # Check companies (tiers)
        companies = Company.objects.all()
        self.stdout.write(
            self.style.SUCCESS(f'Found {companies.count()} investment tiers:')
        )
        
        for company in companies:
            self.stdout.write(
                f'  - {company.name}: R{company.share_price} -> R{company.expected_return} '
                f'({company.duration_days} days)'
            )
        
        # Check investment plans
        plans = InvestmentPlan.objects.all()
        self.stdout.write(
            self.style.SUCCESS(f'\nFound {plans.count()} investment plans:')
        )
        
        # Group plans by phase for better display
        phases = {}
        for plan in plans:
            if plan.phase not in phases:
                phases[plan.phase] = []
            phases[plan.phase].append(plan)
        
        for phase, phase_plans in phases.items():
            self.stdout.write(f'\n  {phase.upper()}:')
            for plan in phase_plans:
                self.stdout.write(
                    f'    - {plan.emoji} {plan.name}: R{plan.min_amount} -> R{plan.return_amount} '
                    f'({plan.get_duration_display()})'
                )
        
        self.stdout.write(
            self.style.SUCCESS('\nVerification complete!')
        )