import os
from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', f"{os.getenv('PROJECT_NAME', 'project')}.settings")

application = get_wsgi_application()

