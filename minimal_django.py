import os
import sys
from django.conf import settings
from django.http import HttpResponse
from django.urls import path
from django.views.decorators.csrf import csrf_exempt

# Minimal Django settings
settings.configure(
    DEBUG=True,
    SECRET_KEY='minimal-secret-key',
    ALLOWED_HOSTS=['localhost', '127.0.0.1'],
    INSTALLED_APPS=[
        'django.contrib.contenttypes',
        'django.contrib.auth',
    ],
    MIDDLEWARE=[
        'django.middleware.security.SecurityMiddleware',
        'django.contrib.sessions.middleware.SessionMiddleware',
        'django.middleware.common.CommonMiddleware',
        'django.middleware.csrf.CsrfViewMiddleware',
        'django.contrib.auth.middleware.AuthenticationMiddleware',
        'django.contrib.messages.middleware.MessageMiddleware',
    ],
    ROOT_URLCONF=__name__,
    USE_TZ=True,
)

from django.core.management import execute_from_command_line

@csrf_exempt
def hello(request):
    return HttpResponse("Hello, World!")

urlpatterns = [
    path('hello/', hello),
]

if __name__ == '__main__':
    execute_from_command_line(sys.argv)