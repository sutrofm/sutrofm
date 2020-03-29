from django.contrib.auth.models import AbstractUser
from django.utils.timezone import now

from django.db import models
from model_utils.fields import AutoCreatedField
from model_utils.models import TimeStampedModel


class User(AbstractUser):
  parties = models.ManyToManyField('Party', through='UserPartyPresence')

  # related fields:
  # messages
  # queued_items
  # votes


class UserPartyPresence(models.Model):
  user = models.ForeignKey('User', on_delete=models.CASCADE)
  party = models.ForeignKey('Party', on_delete=models.CASCADE)

  first_joined = AutoCreatedField()
  last_check_in = models.DateTimeField(default=now)


class Party(TimeStampedModel):
  name = models.CharField(max_length=128)
  playing_item = models.ForeignKey('QueueItem', related_name='playing_party', on_delete=models.DO_NOTHING,
                                   blank=True, null=True)
  theme = models.TextField()

  users = models.ManyToManyField('User', through='UserPartyPresence')


class ChatMessage(TimeStampedModel):
  user = models.ForeignKey('User', on_delete=models.CASCADE, related_name='messages')
  party = models.ForeignKey('Party', on_delete=models.CASCADE)
  message = models.TextField()


class QueueItem(TimeStampedModel):
  service = models.CharField(default='Spotify', max_length=32)
  identifier = models.CharField(max_length=128)
  title = models.TextField()
  artist_name = models.TextField()
  playing_start_time = models.DateTimeField(blank=True)

  user = models.ForeignKey('User', on_delete=models.CASCADE, related_name='queued_items')
  party = models.ForeignKey('Party', on_delete=models.CASCADE, related_name='queue')


class UserVote(TimeStampedModel):
  user = models.ForeignKey('User', on_delete=models.CASCADE, related_name='votes')
  queue_item = models.ForeignKey('QueueItem', on_delete=models.CASCADE, related_name='votes')
  value = models.SmallIntegerField()  # set to 1 or -1 for easy summing
  is_skip = models.BooleanField(default=False)
