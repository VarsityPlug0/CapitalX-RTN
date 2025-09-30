from django.core.management.base import BaseCommand
from core.models import CustomUser

class Command(BaseCommand):
    help = 'Ensure admin user exists with proper permissions'

    def add_arguments(self, parser):
        parser.add_argument('--username', type=str, help='Username for the admin user', default='admin')
        parser.add_argument('--email', type=str, help='Email for the admin user', default='admin@example.com')
        parser.add_argument('--password', type=str, help='Password for the admin user', default='admin123')

    def handle(self, *args, **options):
        username = options['username']
        email = options['email']
        password = options['password']

        # Get or create admin user
        user, created = CustomUser.objects.get_or_create(
            username=username,
            defaults={
                'email': email,
                'is_staff': True,
                'is_superuser': True
            }
        )

        if created:
            user.set_password(password)
            user.save()
            self.stdout.write(
                self.style.SUCCESS(f'Created new admin user: {username}')
            )
        else:
            # Update existing user permissions
            user.is_staff = True
            user.is_superuser = True
            if password:
                user.set_password(password)
            user.save()
            self.stdout.write(
                self.style.SUCCESS(f'Updated existing admin user: {username}')
            )