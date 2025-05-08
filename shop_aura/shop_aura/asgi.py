"""
ASGI config for shop_aura project.
"""

import os

from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'shop_aura.settings')

application = get_asgi_application()
