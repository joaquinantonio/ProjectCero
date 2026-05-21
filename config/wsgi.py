import os

from django.core.wsgi import get_wsgi_application

# Use the development settings by default when running locally
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.dev')

application = get_wsgi_application()

