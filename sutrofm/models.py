from datetime import timedelta, datetime

from django.contrib.auth.models import AbstractUser
from django.db.models import Sum, Value, When, Case, Count
from django.utils.timezone import now

from django.db import models
from model_utils.fields import AutoCreatedField
from model_utils.models import TimeStampedModel

from sutrofm.spotify_api_utils import get_track_duration, get_track_details


class User(AbstractUser):
  parties = models.ManyToManyField('Party', through='UserPartyPresence')

  # related fields:
  # messages
  # queued_items
  # votes

  def check_in_to_party(self, party):
    presence, created = UserPartyPresence.objects.get_or_create(user=self, party=party)
    presence.last_check_in = now()
    presence.save()


class UserPartyPresence(models.Model):
  user = models.ForeignKey('User', on_delete=models.CASCADE)
  party = models.ForeignKey('Party', on_delete=models.CASCADE)

  first_joined = AutoCreatedField()
  last_check_in = models.DateTimeField(default=now)


class Party(TimeStampedModel):
  name = models.CharField(max_length=128, db_index=True)
  playing_item = models.ForeignKey('QueueItem', related_name='playing_party', on_delete=models.SET_NULL,
                                   blank=True, null=True)
  theme = models.TextField()

  users = models.ManyToManyField('User', through='UserPartyPresence')

  def play_next_queue_item(self):
    '''
    Take next item in queue and set as playing item, delete the previously playing obj, and prep queue item for playback
    :return:
    '''
    prev_item = self.playing_item
    self.playing_item = QueueItem.get_next(self)
    if prev_item:
      prev_item.delete()
    if self.playing_item:
      self.playing_item.start_playing()
    self.save()

  def get_player_state_payload(self):
    playing_item = self.playing_item
    if playing_item:
        position, duration = playing_item.get_track_position()
        return {
            'playing_track_position': position / 1000,
            'playing_track_key': playing_item.identifier,
            'playing_track_user_key': playing_item.user.username,
        }
    else:
        return {}

  def get_queue_state_payload(self):
    return [
        item.to_object() for item in self.queue.all()
    ]

  def get_messages_state_payload(self):
    return [
      # Chat message
      {
        'message_type': 'chat',
        'user_id': '123',
        'text': 'Hello world'
      } if i % 2 == 0 else { # New song message
        'message_type': 'new_track',
        'text': "Now playing: Zoopadoop",
        'track_key': 'abc123',
        'track_url': "http://google.com",
        'icon_url': "/static/img/icons/husky.jpeg",
        'track_title': "The Quick Brown Fox Blues"
      } for i in range(10)
    ]

  def get_user_list_state_payload(self):
    return [
        {
          'id': '123',
          'is_active': True,
          'display_name': "marek",
          "user_url": "http://yahoo.com",
          "icon": "/static/img/icons/raccoon.jpeg"
        } for i in range(10)
    ]

  def playing_track_is_over(self):
    return

  def user_count(self):
    return self.users.count()

  def __str__(self):
    return self.name


class ChatMessage(TimeStampedModel):
  user = models.ForeignKey('User', on_delete=models.CASCADE, related_name='messages')
  party = models.ForeignKey('Party', on_delete=models.CASCADE, related_name='messages')
  message = models.TextField()


class QueueItem(TimeStampedModel):
  service = models.CharField(default='Spotify', max_length=32)
  identifier = models.CharField(max_length=128)
  title = models.TextField(default='')
  artist_name = models.TextField(default='')
  playing_start_time = models.DateTimeField(blank=True, null=True)
  duration_ms = models.IntegerField(blank=True, null=True)

  user = models.ForeignKey('User', on_delete=models.CASCADE, related_name='queued_items')
  party = models.ForeignKey('Party', on_delete=models.CASCADE, related_name='queue')

  def to_object(self):
      return {
          'track_key': self.identifier,
          'queue_entry_id': self.id,
          'submitter': self.user.id,
          'upvotes': sum(vote.value for vote in self.votes.all() if vote.value > 0),
          'downvotes': sum(vote.value for vote in self.votes.all() if vote.value < 0),
          'user_key': self.user.username,
      }

  def start_playing(self):
    if not self.duration_ms:
      self.duration_ms = get_track_duration(self.identifier)
    self.playing_start_time = now()
    self.save()

  def save(self, *args, **kwargs):
      # Creating a new queue item
      if not self.id:
          self.hydrate()
      super(QueueItem, self).save(*args, **kwargs)

  def hydrate(self):
      details = get_track_details(self.identifier)
      self.title = details['name']
      self.artist_name = ', '.join([artist['name'] for artist in details['artists']])
      self.duration_ms = details['duration_ms']

  def get_track_position(self):
    """
    Get tuple with (time_played_ms, total_duration_ms).
    """
    if not self.duration_ms:
      return 0, 0

    if not self.playing_start_time:
      return 0, self.duration_ms

    position = now() - self.playing_start_time
    if position > timedelta(microseconds=self.duration_ms*1000):
      # track ended
      return self.duration_ms, self.duration_ms
    else:
      return position.total_seconds()*1000, self.duration_ms

  def vote_score(self):
    return self.votes.aggregate(vote_sum=Sum('value'))['vote_sum'] or 0

  def should_skip(self):
    user_count = self.party.user_count()
    skip_count = self.votes.aggregate(skip_count=Count(Case(When(is_skip=True, then=Value(1)))))['skip_count']
    return skip_count > (user_count / 2)

  @staticmethod
  def get_next(party):
    return QueueItem.list_for_party_queryset(party).first()

  @staticmethod
  def list_for_party_queryset(party):
    # TODO: order by sum of votes -- may want to automatically cache them on the QueueItem
    return QueueItem.objects.filter(party=party, playing_start_time=None).order_by('created')

  def __str__(self):
    return f'{self.identifier}: {self.artist_name} - {self.title}'


class UserVote(TimeStampedModel):
  user = models.ForeignKey('User', on_delete=models.CASCADE, related_name='votes')
  queue_item = models.ForeignKey('QueueItem', on_delete=models.CASCADE, related_name='votes')
  value = models.SmallIntegerField()  # set to 1 or -1 for easy summing
  is_skip = models.BooleanField(default=False)
