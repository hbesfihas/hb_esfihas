# Arquivo: cardapio/consumers.py

import json
from channels.generic.websocket import AsyncWebsocketConsumer

class ManagerConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        user = self.scope["user"]
        if user.is_authenticated and user.is_staff:
            self.room_group_name = 'gerentes'
            await self.channel_layer.group_add(self.room_group_name, self.channel_name)
            await self.accept()
        else:
            await self.close()

    async def disconnect(self, close_code):
        if hasattr(self, 'room_group_name'):
            await self.channel_layer.group_discard(
                self.room_group_name,
                self.channel_name
            )

    # Este método lida com a notificação de um NOVO pedido
    async def novo_pedido(self, event):
        pedido_html = event['pedido_html']
        await self.send(text_data=json.dumps({
            'type': 'new_order',
            'pedido_html': pedido_html
        }))

    async def store_status_update(self, event):
            message_content = event['message']
            await self.send(text_data=json.dumps({
                'type': 'store_status_update',
                'message': message_content
            }))
