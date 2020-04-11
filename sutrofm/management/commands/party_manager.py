import logging
import time
import traceback
from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils.timezone import now

from sutrofm.models import Party, UserPartyPresence

logger = logging.getLogger(__name__)

USER_CHECK_IN_FREQUENCY = timedelta(minutes=1)
WAIT_FOR_USERS = timedelta(minutes=5)
TICK_FREQUENCY = 1  # seconds


class Command(BaseCommand):
  def add_arguments(self, parser):
    parser.add_argument('party_id', type=str)

  def __init__(self, *args, **kwargs):
    super(Command, self).__init__(*args, **kwargs)
    self.redis = None
    self.party = None
    self.party_id = None
    self.keep_running = True

  def handle(self, party_id, *args, **kwargs):
    self.party_id = party_id
    self.party = Party.objects.get(id=party_id)

    self.update_track()

    self.run()

  def run(self):
    logger.info(f'Starting up party manager for "{self.party_id}"!')
    while self.keep_running:
      try:
        self.tick()
        self.keep_running = self.should_keep_running()
      except Exception as ex:
        print(ex)
        print(traceback.format_exc())
        logger.exception("!!! ALERT !!! Room manager... More like room blam-ager.")
      time.sleep(TICK_FREQUENCY)
    else:
      logger.debug('Nobody in room %s, killing' % self.party_id)
      self.party.delete()

  def update_track(self):
    queue_size = self.party.queue.count()

    if not self.party.playing_item and not queue_size:
      logger.info('No tracks queued, nothing to do')
      return

    if not self.party.playing_item and queue_size:
      logger.info('No currently playing track, playing next in queue')
      self.party.play_next_queue_item()

    position_ms, duration_ms = self.party.playing_item.get_track_position()
    # broadcast track position update?
    logger.info(f'Track position {position_ms}ms of {duration_ms}ms total')

    if position_ms == duration_ms or self.party.playing_item.should_skip():
      self.party.play_next_queue_item()


  def tick(self):
    # Refresh the party data
    self.party.refresh_from_db()
    self.update_track()
    self.prune_users()

  def should_keep_running(self):
    return self.party.user_count()

  def prune_users(self):
    UserPartyPresence.objects.filter(party=self.party, last_check_in__lt=now() - USER_CHECK_IN_FREQUENCY).delete()
