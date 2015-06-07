from datetime import datetime, timedelta
import logging
import time

from django.core.management.base import BaseCommand
from django.conf import settings
from rdioapi import Rdio
import logging
import time
from dateutil import parser

from redis import ConnectionPool, StrictRedis

from sutrofm.redis_models import Party

redis_connection_pool = ConnectionPool(**settings.WS4REDIS_CONNECTION)

RDIO_OAUTH2_KEY = 'c2y48bscf6hpd768b6cwvafy'
RDIO_OAUTH2_SECRET = 'sHf9GavUrP'

WAIT_FOR_USERS = timedelta(minutes=5)


class Command(BaseCommand):
  def add_arguments(self, parser):
    parser.add_argument('room_id', type=str)

  def __init__(self, *args, **kwargs):
    super(Command, self).__init__(*args, **kwargs)
    self.party_id = None
    self.currently_playing = None
    self.current_track_duration = None
    self.current_start_time = None
    self.keep_running = True

  def handle(self, room_id, *args, **kwargs):
    self.rdio = Rdio(RDIO_OAUTH2_KEY, RDIO_OAUTH2_SECRET, {})
    self.party_id = room_id
    self.redis = StrictRedis(connection_pool=redis_connection_pool)
    self.party = Party.get(self.redis, room_id)

    self.currently_playing = None
    self.current_track_duration = None
    self.current_start_time = None

    if self.party.playing_track_key:
      track_key = self.party.playing_track_key
      rdio_response = self.rdio.get(keys=track_key)
      if track_key in rdio_response:
        self.current_track_duration = rdio_response[track_key]['duration']
        self.current_start_time = self.party.playing_track_start_time
        self.currently_playing = track_key

    self.run()

  def run(self):
    while self.keep_running:
      try:
        self.keep_running = self.tick()
      except Exception:
        logging.exception("AH DAEMON PROBLEM")
      time.sleep(1)

  def play_next_track(self):
    # Refresh party data
    self.party.play_next_track()
    self.party.save(self.redis)
    self.party.broadcast_player_state(self.redis)

    # TODO replace with redis messages when that patch lands
    if self.party.playing_track_key:
      track_key = self.party.playing_track_key
      rdio_track = self.rdio.get(keys=track_key)[track_key]
      self.currently_playing = track_key
      self.current_track_duration = rdio_track['duration']
      self.current_start_time = self.party.playing_track_start_time
      self.send_play_track_message(rdio_track)
    else:
      self.current_track_duration = None
      self.current_start_time = None
      self.currently_playing = None

  def send_play_track_message(self, rdio_track):
    pass # TODO

  def should_skip(self):
    return len(self.get_skippers()) > len(self.get_online_users()) / 2

  def tick(self):
    # Refresh the party data
    self.party = Party.get(self.redis, self.party_id)

    position = (datetime.utcnow() - (self.current_start_time or datetime.utcnow())).seconds
    if not self.currently_playing or position > self.current_track_duration or self.party.should_skip():
      self.play_next_track()
    return self.should_keep_running()

  def should_keep_running(self):
    """ Kill if no one is online in the room any more """
    return True # TODO when User models are more fleshed out
