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

application = get_wsgi_application()
# Serve both static and media files with Whitenoise
application = WhiteNoise(application, root=settings.MEDIA_ROOT, prefix=settings.MEDIA_URL)
application.add_files(settings.STATIC_ROOT, prefix=settings.STATIC_URL)
