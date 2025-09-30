from django.core.management.base import BaseCommand
from core.models import CustomUser

class Command(BaseCommand):
    help = 'Create a superuser programmatically'

    def add_arguments(self, parser):
        parser.add_argument('--username', type=str, help='Username for the superuser', required=True)
        parser.add_argument('--email', type=str, help='Email for the superuser', required=True)
        parser.add_argument('--password', type=str, help='Password for the superuser', required=True)

    def handle(self, *args, **options):
        username = options['username']
        email = options['email']
        password = options['password']

        # Check if user already exists
        if CustomUser.objects.filter(username=username).exists():
            self.stdout.write(
                self.style.WARNING(f'User with username "{username}" already exists')
            )
            return

        if CustomUser.objects.filter(email=email).exists():
            self.stdout.write(
                self.style.WARNING(f'User with email "{email}" already exists')
            )
            return

        # Create superuser
        user = CustomUser.objects.create_superuser(
            username=username,
            email=email,
            password=password
        )

        self.stdout.write(
            self.style.SUCCESS(f'Successfully created superuser: {user.username}')
        )