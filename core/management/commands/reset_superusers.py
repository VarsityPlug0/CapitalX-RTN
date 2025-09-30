from django.core.management.base import BaseCommand
from core.models import CustomUser

class Command(BaseCommand):
    help = 'Remove all superusers and create a new one'

    def add_arguments(self, parser):
        parser.add_argument('--username', type=str, help='Username for the new superuser', required=True)
        parser.add_argument('--email', type=str, help='Email for the new superuser', required=True)
        parser.add_argument('--password', type=str, help='Password for the new superuser', required=True)

    def handle(self, *args, **options):
        username = options['username']
        email = options['email']
        password = options['password']

        # Delete all existing superusers
        superusers = CustomUser.objects.filter(is_superuser=True)
        count = superusers.count()
        
        if count > 0:
            self.stdout.write(
                self.style.WARNING(f'Deleting {count} existing superusers...')
            )
            superusers.delete()
            self.stdout.write(
                self.style.SUCCESS(f'Successfully deleted {count} superusers')
            )
        else:
            self.stdout.write(
                self.style.WARNING('No existing superusers found')
            )

        # Check if user with same username or email already exists
        if CustomUser.objects.filter(username=username).exists():
            self.stdout.write(
                self.style.WARNING(f'User with username "{username}" already exists, deleting...')
            )
            CustomUser.objects.filter(username=username).delete()

        if CustomUser.objects.filter(email=email).exists():
            self.stdout.write(
                self.style.WARNING(f'User with email "{email}" already exists, deleting...')
            )
            CustomUser.objects.filter(email=email).delete()

        # Create new superuser
        user = CustomUser.objects.create_superuser(
            username=username,
            email=email,
            password=password
        )

        self.stdout.write(
            self.style.SUCCESS(f'Successfully created new superuser: {user.username}')
        )