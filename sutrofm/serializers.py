from sutrofm.models import User, Party, ChatMessage, QueueItem, UserVote
from rest_framework import serializers


class UserSerializer(serializers.HyperlinkedModelSerializer):
  class Meta:
    model = User
    fields = ['username', 'parties']


class UserVoteSerializer(serializers.HyperlinkedModelSerializer):
  user = serializers.PrimaryKeyRelatedField(
    queryset=User.objects.all(),
    default=serializers.CurrentUserDefault()
  )

  class Meta:
    model = UserVote
    fields = ['user', 'queue_item', 'value', 'is_skip']


class ChatMessageSerializer(serializers.HyperlinkedModelSerializer):
  user = serializers.PrimaryKeyRelatedField(
    queryset=User.objects.all(),
    default=serializers.CurrentUserDefault()
  )

  party = serializers.PrimaryKeyRelatedField(
    queryset=Party.objects.all()  # TODO: Filter to parties that the user is a member of
  )

  class Meta:
    model = ChatMessage
    fields = ['user', 'message', 'created', 'party']


class QueueItemSerializer(serializers.HyperlinkedModelSerializer):
  user = serializers.PrimaryKeyRelatedField(
    queryset=User.objects.all(),
    default=serializers.CurrentUserDefault()
  )

  should_skip = serializers.SerializerMethodField()

  # TODO: limit to current user's parties
  party = serializers.PrimaryKeyRelatedField(queryset=Party.objects.all())

  votes = UserVoteSerializer(many=True, read_only=True)

  class Meta:
    model = QueueItem
    fields = ['id', 'identifier', 'title', 'artist_name', 'playing_start_time', 'duration_ms', 'user', 'votes', 'should_skip',
              'party', 'vote_score']

  def get_should_skip(self, obj):
    return obj.should_skip()

  def get_vote_score(self, obj):
    return obj.vote_score()


class PartySerializer(serializers.HyperlinkedModelSerializer):
  users = UserSerializer(many=True, read_only=True)
  messages = ChatMessageSerializer(many=True, read_only=True)
  queue = QueueItemSerializer(many=True, read_only=True)
  playing_item = QueueItemSerializer(read_only=True)

  class Meta:
    model = Party
    fields = ['id', 'name', 'playing_item', 'theme', 'users', 'messages', 'queue']

