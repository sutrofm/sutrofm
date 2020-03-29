import logging
import time
import traceback
from datetime import datetime, timedelta

import spotipy
from django.conf import settings
from django.core.management.base import BaseCommand
from django.utils.timezone import now

from sutrofm.models import Party, UserPartyPresence
from sutrofm.spotify_api_utils import get_track_duration

logger = logging.getLogger(__name__)

USER_CHECK_IN_FREQUENCY = timedelta(minutes=1)
WAIT_FOR_USERS = timedelta(minutes=5)
TICK_FREQUENCY = 1  # seconds


class Command(BaseCommand):
  def add_arguments(self, parser):
    parser.add_argument('party_name', type=str)

  def __init__(self, *args, **kwargs):
    super(Command, self).__init__(*args, **kwargs)
    self.redis = None
    self.party = None
    self.party_name = None
    self.currently_playing = None
    self.current_track_duration = None
    self.current_start_time = None
    self.keep_running = True

  def handle(self, party_name, *args, **kwargs):
    self.party_name = party_name
    self.party = Party.objects.get(party_name)

    self.play_track(self.party.playing_track_key)

    self.run()

  def run(self):
    logger.debug('Starting up room manager process for party "%s"!', self.party_name)
    while self.keep_running:
      try:
        self.keep_running = self.tick()
      except Exception as ex:
        print(ex)
        print(traceback.format_exc())
        logger.exception("!!! ALERT !!! Room manager... More like room blam-ager.")
      time.sleep(TICK_FREQUENCY)
    else:
      logger.debug('Nobody in room %s, killing' % self.party_name)

  def play_track(self, track_key):
    self.current_track_duration = None
    self.current_start_time = None
    self.currently_playing = None

    if track_key:
      self.currently_playing = track_key
      self.current_track_duration = get_track_duration(track_key)
      self.current_start_time = self.party.playing_track_start_time

  def play_next_track(self):
    # Refresh party data
    self.party.play_next_track()
    self.party.save(self.redis)

    was_playing = self.currently_playing
    self.play_track(self.party.playing_track_key)
    if was_playing != self.currently_playing:
      self.send_play_track_message(self.currently_playing)
    self.party.broadcast_player_state(self.redis)
    self.party.broadcast_queue_state(self.redis)

  # def send_play_track_message(self, rdio_track_key):
  #   message = Message.make_now_playing_message(self.redis, self.party, rdio_track_key)
  #   message.save(self.redis)
  #   self.party.broadcast_message_added(self.redis, message)

  def tick(self):
    # Refresh the party data
    self.party = Party.get(self.redis, self.party_name)

    position = (datetime.utcnow() - (self.current_start_time or datetime.utcnow())).seconds
    if (not self.currently_playing) or (position > self.current_track_duration) or self.party.should_skip():
      self.play_next_track()

    self.party.broadcast_user_list_state(self.redis)
    return self.should_keep_running()

  def should_keep_running(self):
    """ Kill if no one is online in the room any more """
    self.prune_users()
    return self.party.users.count()

  def prune_users(self):
    UserPartyPresence.objects.filter(party=self.party, last_check_in__lt=now() - USER_CHECK_IN_FREQUENCY).delete()
