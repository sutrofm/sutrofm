from rest_framework import viewsets, permissions
from rest_framework.decorators import action
from rest_framework.response import Response

from sutrofm.models import User, Party, ChatMessage, QueueItem, UserVote
from sutrofm.party_manager_utils import party_needs_new_manager, spawn_new_party_manager
from sutrofm.serializers import UserSerializer, PartySerializer, ChatMessageSerializer, QueueItemSerializer, \
  UserVoteSerializer
from sutrofm.user_presence import refresh_user_presence


class UserViewSet(viewsets.ModelViewSet):
  """
  API endpoint that allows users to be viewed or edited.
  """
  queryset = User.objects.all().order_by('-date_joined')
  serializer_class = UserSerializer
  permission_classes = [permissions.IsAuthenticated]
  lookup_field = 'username'


class PartyViewSet(viewsets.ModelViewSet):
  # TODO: Filtering on no playing song isn't great, but it's easy
  queryset = Party.objects.filter(playing_item__isnull=False).order_by('-created')
  serializer_class = PartySerializer
  permission_classes = [permissions.IsAuthenticated]

  @action(detail=True, methods=['GET'])
  def ping(self, request, *args, **kwargs):
      party_id = kwargs['pk']
      refresh_user_presence(party_id, request.user.id)
      if party_needs_new_manager(party_id):
        spawn_new_party_manager(party_id)
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

  def get_object(self):
    """
    Modified to do a get_or_create so that we can always use the PUT method and specify the user and queue item rather
    than having to look up the pk of the user's past vote, if any. DRF thinks it's always updating.

    This is implemented in a pretty hacky way, would be better if we were validating the request data, and so on.
    """
    queryset = self.get_queryset()

    obj, _ = queryset.get_or_create(user=self.request.user, queue_item_id=self.request.data.get('queue_item'))
    self.check_object_permissions(self.request, obj)
    return obj

  def put(self, request, *args, **kwargs):
    """
    Using put to do an upsert on the user's vote for a queue item
    """
    return self.update(request, *args, **kwargs)

