# asgi.py
import os
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
# Import middleware mới
from chat.middleware import JWTAuthMiddleware 
from chat.routing import websocket_urlpatterns

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'smartlearn.settings')

application = ProtocolTypeRouter({
    'http': get_asgi_application(),
    'websocket': JWTAuthMiddleware( # Thay AuthMiddlewareStack bằng JWTAuthMiddleware
        URLRouter(websocket_urlpatterns)
    ),
})