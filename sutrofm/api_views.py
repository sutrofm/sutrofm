import httplib

from django.conf import settings
from django.http import JsonResponse, HttpResponse, HttpResponseNotFound
from django.views.decorators.csrf import csrf_exempt
from redis import ConnectionPool, StrictRedis

from sutrofm.redis_models import Party, User, Messages


redis_connection_pool = ConnectionPool(**settings.WS4REDIS_CONNECTION)
redis = StrictRedis(connection_pool=redis_connection_pool)


def get_party_by_id(request, party_id):
  party = Party.get(redis, party_id)

  if party:
    return JsonResponse({'results': party.to_dict()})
  else:
    return HttpResponseNotFound()


def parties(request):
  parties = Party.getall(redis)
  data = [party.to_dict() for party in parties]
  return JsonResponse({'results': data})

def users(request):
    users = User.getall(redis)
    data = [
        {
            "id": user.id,
            "displayName": user.display_name,
            "iconUrl": user.icon_url,
            "userUrl": user.user_url,
            "rdioKey": user.rdio_key,
        } for user in users
    ]

    return JsonResponse({'results': data})

def get_user_by_id(request, user_id):
    user = User.get(redis, user_id)
    data = {
        "id": user.id,
        "displayName": user.display_name,
        "iconUrl": user.icon_url,
        "userUrl": user.user_url,
        "rdioKey": user.rdio_key,
    }
    return JsonResponse({'results': data})


def users(request):
  users = User.getall(redis)
  data = [
    {
      "id": user.id,
      "displayName": user.display_name,
      "iconUrl": user.icon_url,
      "userUrl": user.user_url,
      "rdioKey": user.rdio_key,
    } for user in users
  ]
  return JsonResponse({'results': data})


def get_user_by_id(request, user_id):
  user = User.get(redis, user_id)
  data = {
    "id": user.id,
    "displayName": user.display_name,
    "iconUrl": user.icon_url,
    "userUrl": user.user_url,
    "rdioKey": user.rdio_key,
  }
  return JsonResponse({'results': data})


@csrf_exempt
def messages(request, room_id):
  if request.method == "POST":
    post_message(request)

  messages = Messages.get_recent(redis, room_id)

  return JsonResponse({'results': messages})


def post_message(request):
  party_id = request.POST.get('partyId')  # TODO This should come from the url
  message = request.POST.get('message')
  message_type = request.POST.get('messageType')
  user = request.POST.get('userId')  # TODO this should come from the session

  m = Messages()
  m.save_message(redis, message, message_type, user, party_id)

  return HttpResponse(status=httplib.CREATED)
