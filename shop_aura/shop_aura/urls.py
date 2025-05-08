"""
URL configuration for shop_aura project.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings  # Add this import
from django.conf.urls.static import static
from store.views import test_email  # Assuming this is still needed

urlpatterns = [
     path('', include('store.urls')),
    path('django-admin/', admin.site.urls),


    path('test-email/', test_email, name='test_email'),
]

# Serve media files during development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)