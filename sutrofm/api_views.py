from django.conf import settings
from django.http import JsonResponse
from redis import ConnectionPool, StrictRedis

from sutrofm.redis_models import Party, User

redis_connection_pool = ConnectionPool(**settings.WS4REDIS_CONNECTION)

JSON_MEDIA_TYPE = 'application/json'

def parties(request):
    redis = StrictRedis(connection_pool=redis_connection_pool)
    parties = Party.getall(redis)
    data = [
        {
            "id": party.id,
            "name": party.name,
            "people": [{'id': user.id, 'displayName': user.display_name} for user in party.users],
            "player": {
                "playingTrack": ({
                    "trackKey": party.playingTrackId
                } if party.playingTrackId else None)
            } 
        } for party in parties
    ]
    return JsonResponse(data)

def users(request):
    redis = StrictRedis(connection_pool=redis_connection_pool)
    users = User.getall(redis)
    data = [
        {
            "id": user.id,
            "displayName": user.displayName,
            "iconUrl": user.iconUrl,
            "userUrl": user.userUrl,
            "rdioKey": user.rdioKey,
        } for user in users
    ]
    return JsonResponse(data)

def get_user_by_id(request, user_id):
    redis = StrictRedis(connection_pool=redis_connection_pool)
    user = User.get(redis, user_id)
    data = {
        "id": user.id,
        "displayName": user.displayName,
        "iconUrl": user.iconUrl,
        "userUrl": user.userUrl,
        "rdioKey": user.rdioKey,
    }
    return JsonResponse(data)



