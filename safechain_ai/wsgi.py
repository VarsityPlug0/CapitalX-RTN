"""
WSGI config for aicryptovault project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.1/howto/deployment/wsgi/
"""

import os

from django.core.wsgi import get_wsgi_application
from whitenoise import WhiteNoise
from django.conf import settings

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'safechain_ai.settings')

# Get the Django application
django_application = get_wsgi_application()

# Serve both static and media files with Whitenoise
application = WhiteNoise(django_application)
# Add static files support
application.add_files(settings.STATIC_ROOT, prefix=settings.STATIC_URL.strip('/'))
# Add media files support with correct prefix
application.add_files(settings.MEDIA_ROOT, prefix=settings.MEDIA_URL.strip('/'))
# Additional Whitenoise configuration
application.allow_all_origins = True
application.autorefresh = True

# Configure Whitenoise to handle media files properly
# This ensures that media files are served with the correct content types
application.charset = 'utf-8'