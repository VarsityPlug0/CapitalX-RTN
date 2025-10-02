from django.core.management.base import BaseCommand
from django.conf import settings
import os

class Command(BaseCommand):
    help = 'Debug media settings and file paths'

    def handle(self, *args, **options):
        self.stdout.write("=== Media Settings Debug ===")
        self.stdout.write(f"MEDIA_ROOT: {settings.MEDIA_ROOT}")
        self.stdout.write(f"MEDIA_URL: {settings.MEDIA_URL}")
        self.stdout.write(f"STATIC_ROOT: {settings.STATIC_ROOT}")
        self.stdout.write(f"STATIC_URL: {settings.STATIC_URL}")
        
        # Check if media directory exists
        if os.path.exists(settings.MEDIA_ROOT):
            self.stdout.write(f"MEDIA_ROOT exists: True")
            # List subdirectories
            try:
                subdirs = [d for d in os.listdir(settings.MEDIA_ROOT) if os.path.isdir(os.path.join(settings.MEDIA_ROOT, d))]
                self.stdout.write(f"Media subdirectories: {subdirs}")
                
                # Check specific subdirectories
                for subdir in subdirs:
                    subdir_path = os.path.join(settings.MEDIA_ROOT, subdir)
                    if os.path.exists(subdir_path):
                        files = os.listdir(subdir_path)
                        self.stdout.write(f"  {subdir}/: {len(files)} files")
                        # Show first few files
                        for file in files[:3]:
                            self.stdout.write(f"    - {file}")
            except Exception as e:
                self.stdout.write(f"Error listing media directory: {e}")
        else:
            self.stdout.write(f"MEDIA_ROOT exists: False")
        
        # Test a specific file path
        test_path = os.path.join(settings.MEDIA_ROOT, 'vouchers')
        if os.path.exists(test_path):
            self.stdout.write(f"Vouchers directory exists: True")
            try:
                files = os.listdir(test_path)
                self.stdout.write(f"Voucher files: {len(files)}")
                for file in files[:5]:  # Show first 5 files
                    file_path = os.path.join(test_path, file)
                    if os.path.exists(file_path):
                        size = os.path.getsize(file_path)
                        self.stdout.write(f"  - {file} ({size} bytes)")
            except Exception as e:
                self.stdout.write(f"Error listing vouchers directory: {e}")
        else:
            self.stdout.write(f"Vouchers directory exists: False")
        
        self.stdout.write("=== End Debug ===")