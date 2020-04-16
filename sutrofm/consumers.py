from asgiref.sync import async_to_sync
from channels.generic.websocket import JsonWebsocketConsumer

class PartyConsumer(JsonWebsocketConsumer):
    groups = ['party']

    def connect(self):
        self.party_id = self.scope['url_route']['kwargs']['party_id']
        self.party_group_name = 'party_%s' % self.party_id
        async_to_sync(self.channel_layer.group_add)(self.party_group_name, self.channel_name)
        self.accept()

    def receive_json(self, content):
        async_to_sync(self.channel_layer.group_send)(
            self.party_group_name,
            {
                'type': 'message',
                'content': content
            }
        )

    def message(self, event):
        self.send_json(event['content'])

    def disconnect(self, close_code):
        # Leave party group
        async_to_sync(self.channel_layer.group_discard)(
            self.party_group_name,
            self.channel_name
        )
