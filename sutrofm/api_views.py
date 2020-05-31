from datetime import timedelta

from django.utils.timezone import now
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
  # Party modified should get regularly updated as long as it's active
  queryset = Party.objects.filter(modified__gte=now() - timedelta(minutes=120)).order_by('-modified')
  serializer_class = PartySerializer
  permission_classes = [permissions.IsAuthenticated]

  def perform_update(self, serializer):
    # NOTE: serializer.instance gets updated after calling save
    # if you want to use the old_obj after saving the serializer you should
    # use self.get_object() to get the old instance.
    # other wise serializer.instance would do fine
    old_obj = self.get_object()
    new_data_dict = serializer.validated_data
    theme_changed = False
    # pre save logic
    if old_obj.theme != new_data_dict['theme']:
      theme_changed = True
    new_obj = serializer.save()
    # post save logic
    if theme_changed:
      new_obj.broadcast_theme_changed()

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

