import logging
import threading

import redis
from django.conf import settings
from django.core.management import call_command

logger = logging.getLogger(__name__)

r = redis.from_url(settings.REDIS_URL)


def party_needs_new_manager(party_id):
  return not bool(r.get(f'p{party_id}:manager'))


def spawn_new_party_manager(party_id):
  logger.debug('Spawning party manager for party %s' % party_id)
  party_manager_thread = threading.Thread(target=call_command, args=('party_manager', party_id))
  party_manager_thread.start()
