from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from os import sys
from debug_toolbar.toolbar import debug_toolbar_urls
from django.conf.urls.static import static
from django.contrib.staticfiles.urls import staticfiles_urlpatterns

urlpatterns = [
    path('admin/', admin.site.urls, name='admin'),
    path('', include("a_main.urls")),
    # path('', include("a_stripe.urls")),
]

# Serving the media files in development mode and enabling ddtb

DEBUG_MODE = settings.DEBUG and "test" not in sys.argv
if DEBUG_MODE:
    urlpatterns += static(settings.MEDIA_URL,
                          document_root=settings.MEDIA_ROOT)
    urlpatterns += debug_toolbar_urls()
else:
    urlpatterns += staticfiles_urlpatterns()
