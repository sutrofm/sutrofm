import logging

import redis
from django.conf import settings


USER_PRESENCE_TTL_SEC = 60

logger = logging.getLogger(__name__)

r = redis.from_url(settings.REDIS_URL)


def refresh_user_presence(party_id, user_id):
  logger.info(f'Refreshing presence of user {user_id} in party {party_id}')
  r.set(f'p{party_id}:presence:u{user_id}', '', ex=USER_PRESENCE_TTL_SEC)


def _get_active_user_keys_for_party_id(party_id):
  return r.scan_iter(match=f'p{party_id}:presence:u*')


def get_active_user_ids_for_party_id(party_id):
  return list(int(key.split(b':u')[-1]) for key in _get_active_user_keys_for_party_id(party_id))

