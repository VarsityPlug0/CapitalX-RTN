from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.test import RequestFactory
from django.contrib.sessions.middleware import SessionMiddleware
from django.contrib.auth.middleware import AuthenticationMiddleware
from django.contrib.auth import login
import os
import django
from django.conf import settings

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'safechain_ai.settings')
django.setup()

User = get_user_model()

class Command(BaseCommand):
    help = 'Test admin session handling'

    def handle(self, *args, **options):
        # Create a request factory
        factory = RequestFactory()
        
        # Create a test admin user
        try:
            admin_user = User.objects.get(email='mukoni@gmail.com')
            self.stdout.write(f'Found existing admin user: {admin_user.email}')
        except User.DoesNotExist:
            admin_user = User.objects.create_superuser(
                username='mukoni@gmail.com',
                email='mukoni@gmail.com',
                password='testpass123'
            )
            self.stdout.write(f'Created admin user: {admin_user.email}')
        
        # Create a test request
        request = factory.get('/capitalx_admin/core/deposit/')
        
        # Add session middleware
        session_middleware = SessionMiddleware(lambda req: None)
        session_middleware.process_request(request)
        
        # Add authentication middleware
        auth_middleware = AuthenticationMiddleware(lambda req: None)
        auth_middleware.process_request(request)
        
        # Log in the admin user
        login(request, admin_user)
        
        self.stdout.write(f'User authenticated: {request.user.is_authenticated}')
        self.stdout.write(f'User is admin: {request.user.is_staff}')
        self.stdout.write(f'Session key: {request.session.session_key}')
        
        # Test accessing a client URL
        client_request = factory.get('/dashboard/')
        session_middleware.process_request(client_request)
        auth_middleware.process_request(client_request)
        login(client_request, admin_user)
        
        self.stdout.write(f'Client URL access - User authenticated: {client_request.user.is_authenticated}')
        
        self.stdout.write(
            self.style.SUCCESS('Admin session test completed!')
        )