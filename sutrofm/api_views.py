import simplejson

from django.conf import settings
from django.http import HttpResponse
from redis import ConnectionPool, StrictRedis

from sutrofm.redis_models import Party

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
