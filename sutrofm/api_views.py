import datetime
import httplib

from django.conf import settings
from django.http import JsonResponse, HttpResponse, HttpResponseNotFound
from django.views.decorators.csrf import csrf_exempt
from redis import ConnectionPool, StrictRedis

from sutrofm.redis_models import Party, User, Message


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
    user.to_dict() for user in users
  ]
  return JsonResponse({'results': data})

def get_user_by_id(request, user_id):
    user = User.get(redis, user_id)
    return JsonResponse({'results': user.to_dict()})

def get_party_queue(request, party_id):
  redis = StrictRedis(connection_pool=redis_connection_pool)
  party = Party.get(redis, party_id)

  if party:
    results_list = party.queue_to_dict()
    return JsonResponse({'results': results_list})
  else:
    return HttpResponseNotFound()

@csrf_exempt
def add_to_queue(request, party_id):
  if request.method == "POST":
    redis = StrictRedis(connection_pool=redis_connection_pool)
    user = User.from_request(redis, request)
    party = Party.get(redis, party_id)
    party.enqueue_song(user, request.POST.get('trackKey'))

    party.save(redis)
    party.broadcast_queue_state(redis)
    return JsonResponse({'success': True})
  else:
    return HttpResponseNotFound()

@csrf_exempt
def remove_from_queue(request, party_id):
  if request.method == "POST":
    redis = StrictRedis(connection_pool=redis_connection_pool)
    user = User.from_request(redis, request)
    party = Party.get(redis, party_id)
    queue_entry = party.get_queue_entry(request.POST.get('id'))
    if queue_entry.submitter.id == user.id:
      party.remove_queue_entry(queue_entry)
    party.save(redis)
    party.broadcast_queue_state(redis)
    return JsonResponse({'success': True})
  else:
    return HttpResponseNotFound()

@csrf_exempt
def vote_to_skip(request, party_id):
  if request.method == "POST":
    redis = StrictRedis(connection_pool=redis_connection_pool)
    user = User.from_request(redis, request)
    party = Party.get(redis, party_id)
    party.vote_to_skip(user)
    party.save(redis)
    return JsonResponse({'success': True})
  else:
    return HttpResponseNotFound()

@csrf_exempt
def upvote(request, party_id):
  if request.method == "POST":
    redis = StrictRedis(connection_pool=redis_connection_pool)
    user = User.from_request(redis, request)
    party = Party.get(redis, party_id)
    queue_entry = party.get_queue_entry(request.POST.get('id'))
    queue_entry.upvote(user)
    party.save(redis)
    party.broadcast_queue_state(redis)
    return JsonResponse({'success': True})
  else:
    return HttpResponseNotFound()

@csrf_exempt
def downvote(request, party_id):
  if request.method == "POST":
    redis = StrictRedis(connection_pool=redis_connection_pool)
    user = User.from_request(redis, request)
    party = Party.get(redis, party_id)
    queue_entry = party.get_queue_entry(request.POST.get('id'))
    queue_entry.downvote(user)
    party.save(redis)
    party.broadcast_queue_state(redis)
    return JsonResponse({'success': True})
  else:
    return HttpResponseNotFound()

@csrf_exempt
def ping(request):
  user = User.from_request(redis, request)
  if user:
    user.last_check_in = datetime.datetime.utcnow()
    user.save(redis)
    return JsonResponse({'success': True})
  else:
    return HttpResponseNotFound()

@csrf_exempt
def get_party_users(request, party_id):
  party = Party.get(redis, party_id)

  if party:
    results = party.users_to_dict()
    return JsonResponse({'results': results})
  else:
    return HttpResponseNotFound()


@csrf_exempt
def messages(request, party_id):
  if request.method == "POST":
    post_message(request, party_id)

  messages = Message.get_recent(redis, party_id)
  dict_messages = [
    message.to_dict() for message in messages
  ]

  return JsonResponse({'results': dict_messages})


def post_message(request, party_id):
  message_type = request.POST.get('messageType')
  user = User.from_request(redis, request)
  party = Party.get(redis, party_id)

  m = Message.for_party(redis, party)

  if message_type == 'chat':
    text = request.POST.get('text')
    m.text = text

  if message_type == 'favorite':
    track = request.POST.get('trackKey')
    m.track = track

  if message_type == 'vote_to_skip':
    track = request.POST.get('trackKey')
    m.track = track

  m.user_key = user.rdio_key
  m.message_type = message_type
  m.save(redis)

  party.add_message(m)
  party.save(redis)

  party.broadcast_message_added(redis, m)

  return HttpResponse(status=httplib.CREATED)
