import json
from channels.generic.websocket import AsyncWebsocketConsumer


class OrdenConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.orden_id = self.scope['url_route']['kwargs']['orden_id']
        self.group_name = f'orden_{self.orden_id}'
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def orden_actualizada(self, event):
        await self.send(text_data=json.dumps({
            'estado': event['estado'],
            'tecnico_nombre': event.get('tecnico_nombre'),
        }))