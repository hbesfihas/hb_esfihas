from django.urls import path
from . import consumers

websocket_urlpatterns = [
    path('ws/painel-gerente/', consumers.ManagerConsumer.as_asgi()),
]