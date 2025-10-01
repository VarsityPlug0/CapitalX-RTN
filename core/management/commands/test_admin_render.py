from django.core.management.base import BaseCommand
from django.test import RequestFactory
from core.views import admin_dashboard_view
from core.models import CustomUser
from django.contrib.auth.models import AnonymousUser
from django.contrib.sessions.middleware import SessionMiddleware
from django.contrib.auth.middleware import AuthenticationMiddleware
from django.http import HttpResponse

class Command(BaseCommand):
    help = 'Test admin dashboard rendering'

    def handle(self, *args, **options):
        try:
            # Create a request factory
            factory = RequestFactory()
            
            # Create a request
            request = factory.get('/admin_dashboard/')
            
            # Add session (simplified for testing)
            from django.contrib.sessions.backends.db import SessionStore
            request.session = SessionStore()
            request.session.create()
            
            # Create an admin user and authenticate
            admin_user = CustomUser.objects.get(email='admin@example.com')
            request.user = admin_user
            
            # Call the view
            response = admin_dashboard_view(request)
            
            # Check response
            if isinstance(response, HttpResponse):
                self.stdout.write(
                    self.style.SUCCESS(f'View rendered successfully with status code: {response.status_code}')
                )
                if response.status_code == 200:
                    self.stdout.write('Content preview (first 500 chars):')
                    self.stdout.write(str(response.content[:500]))
            else:
                self.stdout.write(
                    self.style.ERROR(f'View returned unexpected response type: {type(response)}')
                )
                
        except CustomUser.DoesNotExist:
            self.stdout.write(
                self.style.ERROR('Admin user not found')
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error during view rendering: {str(e)}')
            )
            import traceback
            traceback.print_exc()