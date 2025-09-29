from django.core.management.base import BaseCommand
from core.models import Company
from decimal import Decimal

class Command(BaseCommand):
    help = 'Create investment tiers for the CapitalX platform'

    def handle(self, *args, **options):
        # Define the investment tiers as specified
        tiers = [
            {
                'name': 'Foundation Tier',
                'share_price': Decimal('70.00'),
                'expected_return': Decimal('1120.00'),
                'duration_days': 7,
                'min_level': 1,
                'description': 'Beginner Friendly - Investment range: R70 - R1,120'
            },
            {
                'name': 'Growth Tier',
                'share_price': Decimal('2240.00'),
                'expected_return': Decimal('17920.00'),
                'duration_days': 14,
                'min_level': 1,
                'description': 'Intermediate - Investment range: R2,240 - R17,920'
            },
            {
                'name': 'Premium Tier',
                'share_price': Decimal('35840.00'),
                'expected_return': Decimal('50000.00'),
                'duration_days': 30,
                'min_level': 1,
                'description': 'Advanced - Investment range: R35,840 - R50,000'
            },
        ]

        # Create or update the tiers
        for tier_data in tiers:
            tier, created = Company.objects.update_or_create(
                name=tier_data['name'],
                defaults={
                    'share_price': tier_data['share_price'],
                    'expected_return': tier_data['expected_return'],
                    'duration_days': tier_data['duration_days'],
                    'min_level': tier_data['min_level'],
                    'description': tier_data['description']
                }
            )
            
            if created:
                self.stdout.write(
                    self.style.SUCCESS(f'Created tier: {tier.name}')
                )
            else:
                self.stdout.write(
                    self.style.SUCCESS(f'Updated tier: {tier.name}')
                )

        self.stdout.write(
            self.style.SUCCESS('Successfully created/updated all investment tiers')
        )