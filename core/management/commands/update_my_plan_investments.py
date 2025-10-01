from django.core.management.base import BaseCommand
from core.models import PlanInvestment
from django.utils import timezone
from django.contrib.auth import get_user_model

User = get_user_model()

class Command(BaseCommand):
    help = 'Update plan investments for a specific user that should be completed'

    def add_arguments(self, parser):
        parser.add_argument('username', type=str, help='Username of the user whose investments to update')

    def handle(self, *args, **options):
        username = options['username']
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            self.stdout.write(
                self.style.ERROR(f'User "{username}" does not exist')
            )
            return

        # Get all active plan investments for this user that should be completed
        investments_to_update = PlanInvestment.objects.filter(
            user=user,
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
                    f'Updated investment {investment.id} - {investment.plan.name}'
                )
            )
        
        if updated_count == 0:
            self.stdout.write(
                self.style.WARNING(
                    'No investments needed to be updated'
                )
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(
                    f'Successfully updated {updated_count} plan investments for user {username}'
                )
            )