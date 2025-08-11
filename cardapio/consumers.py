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

  # Este método lida com a notificação de uma ATUALIZAÇÃO DE STATUS
    async def status_update(self, event):
        # Pega a mensagem que veio da view
        message_content = event['message']

        # Retransmite a mensagem para o navegador do gerente
        await self.send(text_data=json.dumps({
            'type': 'status_update',
            'message': message_content
        }))

 # --- MÉTODO PARA ATUALIZAR STATUS DA LOJA ---
    async def store_status_update(self, event):
        # 1. Primeiro, pegue o dicionário 'message' que a view enviou.
        message_content = event['message']

        # 2. Agora, retransmita esse conteúdo para o navegador.
        # O JavaScript no frontend saberá como ler 'message.loja_aberta'.
        await self.send(text_data=json.dumps({
            'type': 'store_status_update',
            'message': message_content
        }))

    async def pedido_cancelado(self, event):
        message_content = event['message']

        #Retransmite a mensagem de cancelamento para o navegador

        await self.send(text_data=json.dumps({
            'type':'pedido_cancelado',
            'message': message_content
        }))
