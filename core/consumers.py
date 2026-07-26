import json
from channels.generic.websocket import AsyncWebsocketConsumer


class StockConsumer(AsyncWebsocketConsumer):
    GROUP_NAME = "stock_updates"

    async def connect(self):
        await self.channel_layer.group_add(self.GROUP_NAME, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.GROUP_NAME, self.channel_name)

    async def receive(self, text_data):
        data = json.loads(text_data)
        await self.channel_layer.group_send(
            self.GROUP_NAME,
            {
                "type": "stock.update",
                "data": data,
            },
        )

    async def stock_update(self, event):
        await self.send(text_data=json.dumps(event["data"]))