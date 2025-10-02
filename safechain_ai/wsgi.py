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
from django.core.files.storage import default_storage
from django.http import HttpResponse, HttpResponseNotFound
from django.urls import resolve
import mimetypes

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'safechain_ai.settings')

# Get the Django application
django_application = get_wsgi_application()

# Custom middleware to serve media files
def media_middleware(application):
    def middleware(environ, start_response):
        # Check if the request is for a media file
        path = environ.get('PATH_INFO', '')
        if path.startswith(settings.MEDIA_URL):
            # Remove the MEDIA_URL prefix to get the file path
            file_path = path[len(settings.MEDIA_URL):]
            # Construct the full file path
            full_path = os.path.join(settings.MEDIA_ROOT, file_path)
            
            # Check if the file exists
            if os.path.exists(full_path) and os.path.isfile(full_path):
                # Determine content type
                content_type, _ = mimetypes.guess_type(full_path)
                if content_type is None:
                    content_type = 'application/octet-stream'
                
                # Read and serve the file
                try:
                    with open(full_path, 'rb') as f:
                        content = f.read()
                    
                    # Create response
                    response = HttpResponse(content, content_type=content_type)
                    response['Content-Length'] = str(len(content))
                    
                    # Start response
                    status = '{} {}'.format(response.status_code, response.reason_phrase)
                    headers = list(response.items())
                    start_response(status, headers)
                    return [content]
                except Exception as e:
                    # If there's an error reading the file, fall back to Django
                    pass
        
        # For all other requests, use the normal Django application
        return application(environ, start_response)
    
    return middleware

# Serve both static and media files
application = WhiteNoise(django_application)
# Add static files support
application.add_files(settings.STATIC_ROOT, prefix=settings.STATIC_URL.strip('/'))

# Wrap with our custom media middleware
application = media_middleware(application)