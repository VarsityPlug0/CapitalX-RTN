from django.core.management.base import BaseCommand
from django.test import RequestFactory
from django.middleware.csrf import get_token
from django.contrib.sessions.middleware import SessionMiddleware
from django.contrib.auth.middleware import AuthenticationMiddleware
from django.middleware.csrf import CsrfViewMiddleware

class Command(BaseCommand):
    help = 'Debug CSRF issues by testing middleware behavior'

    def handle(self, *args, **options):
        # Create a request factory
        factory = RequestFactory()
        
        # Create a test request
        request = factory.post('/deposit/', {'amount': '100', 'payment_method': 'voucher'})
        
        # Add session middleware
        session_middleware = SessionMiddleware(lambda req: None)
        session_middleware.process_request(request)
        
        # Add authentication middleware (simulate authenticated user)
        # Note: This is a simplified test - in reality, you'd need a real user object
        
        # Add CSRF middleware
        csrf_middleware = CsrfViewMiddleware(lambda req: None)
        
        # Try to get CSRF token
        try:
            token = get_token(request)
            self.stdout.write(f'CSRF Token: {token}')
            self.stdout.write('CSRF token generation: SUCCESS')
        except Exception as e:
            self.stdout.write(f'CSRF token generation failed: {e}')
        
        self.stdout.write(
            self.style.SUCCESS('CSRF debugging completed!')
        )