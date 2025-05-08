"""
WSGI config for shop_aura project.
"""

import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'shop_aura.settings')

application = get_wsgi_application()
