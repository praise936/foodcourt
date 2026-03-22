# backend/asgi.py — ASGI config for WebSockets via Django Channels

import os
from django.core.asgi import get_asgi_application

# Set the settings module FIRST
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')

# Initialize Django ASGI application BEFORE importing other Django modules
django_asgi_app = get_asgi_application()

# Now import other Django-dependent modules
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from channels.security.websocket import AllowedHostsOriginValidator
import notifications.routing

# For development, serve static files through Django's static serving
# In production, you should use a proper web server (nginx, Apache) to serve static files
application = ProtocolTypeRouter({
    'http': django_asgi_app,  # Direct HTTP to Django without WhiteNoise
    'websocket': AllowedHostsOriginValidator(
        AuthMiddlewareStack(
            URLRouter(
                notifications.routing.websocket_urlpatterns
            )
        )
    ),
})