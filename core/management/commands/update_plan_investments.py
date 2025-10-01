from django.core.management.base import BaseCommand
from core.models import PlanInvestment
from django.utils import timezone

class Command(BaseCommand):
    help = 'Update plan investments that should be completed'

    def handle(self, *args, **options):
        # Get all active plan investments that should be completed
        investments_to_update = PlanInvestment.objects.filter(
            is_active=True,
            end_date__lte=timezone.now()
        )
        
        updated_count = 0
        for investment in investments_to_update:
            # Call save to trigger the completion logic
            investment.save()
            updated_count += 1
            self.stdout.write(
                self.style.SUCCESS(
                    f'Updated investment {investment.id} for {investment.user.username} - {investment.plan.name}'
                )
            )
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully updated {updated_count} plan investments'
            )
        )