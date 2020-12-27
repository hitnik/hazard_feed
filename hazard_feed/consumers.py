from channels.generic.websocket import AsyncJsonWebsocketConsumer
from .utils import get_actial_hazard_feeds


class WeatherJsonConsumer(AsyncJsonWebsocketConsumer):
    """
    Websocket works with nex scheme:
        - When socket connected client receive {'response':'ok'}.
        - For nginx keep alive connection (it keep 60 seconds)
        implemented ping option: from client you can send
        {'payload':'ping'} and as a response server will send
        {'response':'ok', 'payload':'pong'}.
        - If you want to get actual weather hazard feeds, you
        would send to server {'payload':'feeds'}. Response will
        be like {'response':'ok', 'payload:': <list of actual feeds>}

    """
    group_name = 'weather'
    response = {'response': 'ok'}
    ping_response = dict(response, payload='pong')
    empty_response = dict(response, payload='empty')

    async def connect(self):

        # Join group
        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name
        )
        await self.accept()

        await self.channel_layer.send(self.channel_name,
            {
              'type': 'weather.notify',
              'content': self.response
            }
        )

    async def disconnect(self, close_code):
        # Leave group
        await self.channel_layer.group_discard(
            self.group_name,
            self.channel_name
        )

    async def receive_json(self, content):
        # receive messages from socket

        if content['payload'] == 'feeds':
            await self.send_weather_response()
            return
        await self.send_ping_response()



    async def send_ping_response(self):
        # send pong message to socket
        await self.channel_layer.send(self.channel_name,
              {
                  'type': 'weather.notify',
                  'content': self.ping_response
              }
              )

    async def send_weather_response(self):
        # send weather message to socket

        feeds = await get_actial_hazard_feeds()
        print(feeds)
        if feeds:
            response = dict(self.response, payload=feeds)
        else:
            response = self.empty_response

        await self.channel_layer.send(self.channel_name,
              {
                  'type': 'weather.notify',
                  'content': response
              }
              )

    async def weather_notify(self, event):
        content = event['content']
        # Send message to WebSocket
        await self.send_json(content=content)