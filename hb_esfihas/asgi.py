import os
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
import cardapio.routing

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hb_esfihas.settings')

# Esta é a configuração padrão. O WhiteNoise funcionará através do middleware.
application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    "websocket": AuthMiddlewareStack(
        URLRouter(
            cardapio.routing.websocket_urlpatterns
        )
    ),
})