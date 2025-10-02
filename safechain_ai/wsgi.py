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

# Serve only static files with Whitenoise, not media files
application = WhiteNoise(django_application)
# Add static files support
application.add_files(settings.STATIC_ROOT, prefix=settings.STATIC_URL.strip('/'))
# Do not add media files here - let our custom middleware handle them