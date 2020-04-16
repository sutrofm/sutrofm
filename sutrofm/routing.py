from channels.routing import ProtocolTypeRouter, URLRouter
from sutrofm.consumers import PartyConsumer
from django.urls import re_path


application = ProtocolTypeRouter({
    # Empty for now (http->django views is added by default)
    'websocket': URLRouter(
        [re_path('ws/party/(?P<party_id>\d+)/$', PartyConsumer)]
    )
})
