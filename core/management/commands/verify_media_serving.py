from django.core.management.base import BaseCommand
from django.test import RequestFactory
from django.conf import settings
import os
from core.middleware import MediaFileMiddleware

class Command(BaseCommand):
    help = 'Verify media file serving is working correctly'

    def handle(self, *args, **options):
        self.stdout.write("=== Media Serving Verification ===")
        
        # Test 1: Check if media files exist
        self.stdout.write("Test 1: Checking media file existence...")
        test_files = [
            'vouchers/Screenshot_2025-10-01_193517.png',
            'deposit_proofs/IMG_3961.jpeg'
        ]
        
        for test_file in test_files:
            file_path = os.path.join(settings.MEDIA_ROOT, test_file)
            if os.path.exists(file_path):
                size = os.path.getsize(file_path)
                self.stdout.write(f"  ✓ {test_file} exists ({size} bytes)")
            else:
                self.stdout.write(f"  ✗ {test_file} NOT FOUND")
        
        # Test 2: Simulate middleware processing
        self.stdout.write("\nTest 2: Simulating middleware processing...")
        factory = RequestFactory()
        
        # Create a mock get_response function
        def get_response(request):
            return None
            
        middleware = MediaFileMiddleware(get_response)
        
        # Test a media request
        test_request = factory.get('/media/vouchers/Screenshot_2025-10-01_193517.png')
        self.stdout.write(f"  Request path: {test_request.path}")
        self.stdout.write(f"  Starts with MEDIA_URL: {test_request.path.startswith(settings.MEDIA_URL)}")
        
        if test_request.path.startswith(settings.MEDIA_URL):
            media_url = settings.MEDIA_URL
            if media_url.endswith('/'):
                file_path = test_request.path[len(media_url):]
            else:
                file_path = test_request.path[len(media_url)+1:]
            
            full_path = os.path.join(settings.MEDIA_ROOT, file_path)
            self.stdout.write(f"  Extracted file path: {file_path}")
            self.stdout.write(f"  Full file path: {full_path}")
            self.stdout.write(f"  File exists: {os.path.exists(full_path)}")
            self.stdout.write(f"  Is file: {os.path.isfile(full_path)}")
        
        self.stdout.write("\n=== Verification Complete ===")
        self.stdout.write("To test actual serving, visit: http://localhost:8000/test-media/")