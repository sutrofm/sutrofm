import simplejson

from django.conf import settings
from django.http import HttpResponse
from redis import ConnectionPool, StrictRedis

from rdiodj.redis_models import Party, Messages


redis_connection_pool = ConnectionPool(**settings.WS4REDIS_CONNECTION)


def parties(request):
    redis = StrictRedis(connection_pool=redis_connection_pool)
    parties = Party.getall(redis)
    data = [
        {
            "id": party.id,
            "name": party.name
        } for party in parties
    ]
    json_string = simplejson.dumps(data)
    return HttpResponse(json_string, content_type='text/json')


def messages(request, room_id):
    redis = StrictRedis(connection_pool=redis_connection_pool)
    messages = Messages.get_recent(redis, room_id)
    json_string = simplejson.dumps(messages)
    return HttpResponse(json_string, content_type='text/json')    