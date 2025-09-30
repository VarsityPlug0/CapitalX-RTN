from django.core.management.base import BaseCommand
from core.models import CustomUser

class Command(BaseCommand):
    help = 'Reset the admin user password'

    def add_arguments(self, parser):
        parser.add_argument('--username', type=str, help='Username for the admin user', default='admin')
        parser.add_argument('--password', type=str, help='New password for the admin user', default='admin123')

    def handle(self, *args, **options):
        username = options['username']
        password = options['password']

        try:
            user = CustomUser.objects.get(username=username)
            user.set_password(password)
            user.save()
            self.stdout.write(
                self.style.SUCCESS(f'Successfully reset password for user: {username}')
            )
        except CustomUser.DoesNotExist:
            self.stdout.write(
                self.style.ERROR(f'User with username "{username}" does not exist')
            )