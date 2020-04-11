from rest_framework import viewsets, permissions
from rest_framework.decorators import action
from rest_framework.response import Response

from sutrofm.models import User, Party, ChatMessage, QueueItem, UserVote
from sutrofm.serializers import UserSerializer, PartySerializer, ChatMessageSerializer, QueueItemSerializer, \
  UserVoteSerializer
from sutrofm.views import make_party_manager


class UserViewSet(viewsets.ModelViewSet):
  """
  API endpoint that allows users to be viewed or edited.
  """
  queryset = User.objects.all().order_by('-date_joined')
  serializer_class = UserSerializer
  permission_classes = [permissions.IsAuthenticated]
  lookup_field = 'username'


class PartyViewSet(viewsets.ModelViewSet):
  # TODO: should probably sort by something smarter than created
  queryset = Party.objects.all().order_by('-created')
  serializer_class = PartySerializer
  permission_classes = [permissions.IsAuthenticated]

  def create(self, request, *args, **kwargs):
    response = super().create(request, *args, **kwargs)
    make_party_manager('asdf')
    return response

  @action(detail=True, methods=['GET'])
  def ping(self, request, *args, **kwargs):
      party = self.get_object()
      request.user.check_in_to_party(party)
      return Response({'hi': 'ok'})

class ChatMessageViewSet(viewsets.ModelViewSet):
  queryset = ChatMessage.objects.all().order_by('-created')
  serializer_class = ChatMessageSerializer
  permission_classes = [permissions.IsAuthenticated]


class QueueItemViewSet(viewsets.ModelViewSet):
  queryset = QueueItem.objects.all().order_by('-created')
  serializer_class = QueueItemSerializer
  permission_classes = [permissions.IsAuthenticated]

class UserVoteViewSet(viewsets.ModelViewSet):
  queryset = UserVote.objects.all().order_by('-created')
  serializer_class = UserVoteSerializer
  permission_classes = [permissions.IsAuthenticated]









# import datetime
#
# from django.conf import settings
# from django.http import HttpResponse, HttpResponseNotFound, JsonResponse
# from django.views.decorators.csrf import csrf_exempt
# from redis import ConnectionPool, StrictRedis
#
# from sutrofm.redis_models import Message, Party, User
#
# redis_connection_pool = ConnectionPool(**settings.WS4REDIS_CONNECTION)
#
#
# def get_party_by_id(request, party_id):
#   redis = StrictRedis(connection_pool=redis_connection_pool)
#   party = Party.get(redis, party_id)
#   if party:
#     return JsonResponse({'results': party.to_dict()})
#   else:
#     return HttpResponseNotFound()
#
#
# def parties(request):
#   redis = StrictRedis(connection_pool=redis_connection_pool)
#   all_parties = Party.getall(redis)
#   data = [party.to_dict() for party in all_parties if party]
#   return JsonResponse({'results': data})
#
#
# def users(request):
#   redis = StrictRedis(connection_pool=redis_connection_pool)
#   users = User.getall(redis)
#   data = [
#     user.to_dict() for user in users
#   ]
#   return JsonResponse({'results': data})
#
#
# def get_user_by_id(request, user_id):
#   redis = StrictRedis(connection_pool=redis_connection_pool)
#   user = User.get(redis, user_id)
#   return JsonResponse({'results': user.to_dict()})
#
#
# def get_party_queue(request, party_id):
#   redis = StrictRedis(connection_pool=redis_connection_pool)
#   party = Party.get(redis, party_id)
#
#   if party:
#     results_list = party.queue_to_dict()
#     return JsonResponse({'results': results_list})
#   else:
#     return HttpResponseNotFound()
#
#
# @csrf_exempt
# def get_theme(request, party_id):
#   redis = StrictRedis(connection_pool=redis_connection_pool)
#   party = Party.get(redis, party_id)
#
#   if party:
#     return JsonResponse({'results': party.theme_to_dict()})
#   else:
#     return HttpResponseNotFound()
#
#
# @csrf_exempt
# def set_theme(request, party_id):
#   if request.method == "POST":
#     redis = StrictRedis(connection_pool=redis_connection_pool)
#     theme = request.POST.get('theme')
#     party = Party.get(redis, party_id)
#     party.theme = theme
#     party.save(redis)
#     party.broadcast_theme_state(redis)
#
#     return JsonResponse({'success': True})
#   else:
#     return HttpResponseNotFound()
#
#
# @csrf_exempt
# def add_to_queue(request, party_id):
#   if request.method == "POST":
#     redis = StrictRedis(connection_pool=redis_connection_pool)
#     user = User.from_request(redis, request)
#     party = Party.get(redis, party_id)
#     party.enqueue_song(user, request.POST.get('trackKey'))
#
#     party.save(redis)
#     party.broadcast_queue_state(redis)
#     return JsonResponse({'success': True})
#   else:
#     return HttpResponseNotFound()
#
#
# @csrf_exempt
# def remove_from_queue(request, party_id):
#   if request.method == "POST":
#     redis = StrictRedis(connection_pool=redis_connection_pool)
#     user = User.from_request(redis, request)
#     party = Party.get(redis, party_id)
#     queue_entry = party.get_queue_entry(request.POST.get('id'))
#     if queue_entry.submitter.id == user.id:
#       party.remove_queue_entry(queue_entry)
#     party.save(redis)
#     party.broadcast_queue_state(redis)
#     return JsonResponse({'success': True})
#   else:
#     return HttpResponseNotFound()
#
#
# @csrf_exempt
# def vote_to_skip(request, party_id):
#   if request.method == "POST":
#     redis = StrictRedis(connection_pool=redis_connection_pool)
#     user = User.from_request(redis, request)
#     party = Party.get(redis, party_id)
#     party.vote_to_skip(user)
#     party.save(redis)
#     return JsonResponse({'success': True})
#   else:
#     return HttpResponseNotFound()
#
#
# @csrf_exempt
# def upvote(request, party_id):
#   if request.method == "POST":
#     redis = StrictRedis(connection_pool=redis_connection_pool)
#     user = User.from_request(redis, request)
#     party = Party.get(redis, party_id)
#     queue_entry = party.get_queue_entry(request.POST.get('id'))
#     queue_entry.upvote(user)
#     party.save(redis)
#     party.broadcast_queue_state(redis)
#     return JsonResponse({'success': True})
#   else:
#     return HttpResponseNotFound()
#
#
# @csrf_exempt
# def downvote(request, party_id):
#   if request.method == "POST":
#     redis = StrictRedis(connection_pool=redis_connection_pool)
#     user = User.from_request(redis, request)
#     party = Party.get(redis, party_id)
#     queue_entry = party.get_queue_entry(request.POST.get('id'))
#     queue_entry.downvote(user)
#     party.save(redis)
#     party.broadcast_queue_state(redis)
#     return JsonResponse({'success': True})
#   else:
#     return HttpResponseNotFound()
#
#
# @csrf_exempt
# def ping(request):
#   redis = StrictRedis(connection_pool=redis_connection_pool)
#   user = User.from_request(redis, request)
#   if user:
#     user.last_check_in = datetime.datetime.utcnow()
#     user.save(redis)
#     return JsonResponse({'success': True})
#   else:
#     return HttpResponseNotFound()
#
#
# @csrf_exempt
# def ping_party(request, party_id):
#   redis = StrictRedis(connection_pool=redis_connection_pool)
#   party = None
#   user = User.from_request(redis, request)
#   if user:
#     party = Party.get(redis, party_id)
#   if user and party:
#     user.visit_party(party_id)
#     user.save(redis)
#     party.add_user(redis, user)
#     return JsonResponse({'success': True})
#   else:
#     return HttpResponseNotFound()
#
#
# @csrf_exempt
# def get_party_users(request, party_id):
#   redis = StrictRedis(connection_pool=redis_connection_pool)
#   party = Party.get(redis, party_id)
#
#   if party:
#     results = party.users_to_dict()
#     return JsonResponse({'results': results})
#   else:
#     return HttpResponseNotFound()
#
#
# @csrf_exempt
# def messages(request, party_id):
#   redis = StrictRedis(connection_pool=redis_connection_pool)
#   if request.method == "POST":
#     post_message(request, party_id)
#
#   messages = Message.get_recent(redis, party_id)
#   dict_messages = [
#     message.to_dict() for message in messages
#   ]
#
#   return JsonResponse({'results': dict_messages})
#
#
# def post_message(request, party_id):
#   redis = StrictRedis(connection_pool=redis_connection_pool)
#   message_type = request.POST.get('messageType')
#   user = User.from_request(redis, request)
#   party = Party.get(redis, party_id)
#
#   m = Message.for_party(redis, party)
#
#   if message_type == 'chat':
#     text = request.POST.get('text')
#     m.text = text
#
#   if message_type == 'favorite':
#     track = request.POST.get('trackKey')
#     m.track = track
#
#   if message_type == 'vote_to_skip':
#     track = request.POST.get('trackKey')
#     m.track = track
#
#   m.user_id = user.id
#   m.message_type = message_type
#   m.save(redis)
#
#   party.broadcast_message_added(redis, m)
#
#   return HttpResponse(status=201)
