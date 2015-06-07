import httplib
from django.conf import settings
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from redis import ConnectionPool, StrictRedis

from sutrofm.redis_models import Party, User, Messages

redis_connection_pool = ConnectionPool(**settings.WS4REDIS_CONNECTION)

def parties(request):
    redis = StrictRedis(connection_pool=redis_connection_pool)
    parties = Party.getall(redis)
    data = [
        {
            "id": party.id,
            "name": party.name,
            "people": [{'id': user.id, 'displayName': user.display_name} for user in party.users],
            "player": {
                "playingTrack": {
                    "trackKey": party.playing_track_id
                }
            }
        } for party in parties
    ]
    return JsonResponse({'results': data})

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

@csrf_exempt
def messages(request, room_id):
    if request.method == "POST":
        post_message(request)

    redis = StrictRedis(connection_pool=redis_connection_pool)
    messages = Messages.get_recent(redis, room_id)

    return JsonResponse(messages)

def post_message(request):
    party_id = request.POST.get('partyId')
    message = request.POST.get('message')
    message_type = request.POST.get('messageType')
    user = request.POST.get('userId')

    m = Messages()
    redis = StrictRedis(connection_pool=redis_connection_pool)
    m.save_message(redis, message, message_type, user, party_id)

    return HttpResponse(status=httplib.CREATED)
