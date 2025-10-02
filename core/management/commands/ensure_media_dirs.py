from django.core.management.base import BaseCommand
from django.conf import settings
import os

class Command(BaseCommand):
    help = 'Ensure media directories exist'

    def handle(self, *args, **options):
        self.stdout.write("=== Ensuring Media Directories Exist ===")
        self.stdout.write(f"MEDIA_ROOT: {settings.MEDIA_ROOT}")
        
        # Ensure media directory exists
        if not os.path.exists(settings.MEDIA_ROOT):
            try:
                os.makedirs(settings.MEDIA_ROOT, exist_ok=True)
                self.stdout.write(f"Created MEDIA_ROOT directory: {settings.MEDIA_ROOT}")
            except Exception as e:
                self.stdout.write(f"Failed to create MEDIA_ROOT directory: {e}")
                return
        else:
            self.stdout.write(f"MEDIA_ROOT directory exists: {settings.MEDIA_ROOT}")
        
        # Ensure subdirectories exist
        media_subdirs = ['vouchers', 'deposit_proofs']
        for subdir in media_subdirs:
            subdir_path = os.path.join(settings.MEDIA_ROOT, subdir)
            if not os.path.exists(subdir_path):
                try:
                    os.makedirs(subdir_path, exist_ok=True)
                    self.stdout.write(f"Created media subdirectory: {subdir_path}")
                except Exception as e:
                    self.stdout.write(f"Failed to create media subdirectory {subdir}: {e}")
            else:
                self.stdout.write(f"Media subdirectory exists: {subdir_path}")
        
        self.stdout.write("=== Media Directories Check Complete ===")