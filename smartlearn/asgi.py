import os
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'smartlearn.settings')

# Import routing sau khi set env
from chat.routing import websocket_urlpatterns as chat_ws
from live_quiz.routing import websocket_urlpatterns as live_ws
from notifications.routing import websocket_urlpatterns as notif_ws

application = ProtocolTypeRouter({
    'http': get_asgi_application(),
    'websocket': AuthMiddlewareStack(
        URLRouter(
            chat_ws + live_ws + notif_ws
        )
    ),
})