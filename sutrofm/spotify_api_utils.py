import logging
from functools import lru_cache

import spotipy
from cachetools import TTLCache, cached

from django.conf import settings


logger = logging.getLogger(__name__)


def get_spotify_api_client():
  client_credentials_manager = spotipy.SpotifyClientCredentials(client_id=settings.SOCIAL_AUTH_SPOTIFY_KEY,
                                                                client_secret=settings.SOCIAL_AUTH_SPOTIFY_SECRET)
  return spotipy.Spotify(client_credentials_manager=client_credentials_manager)


def get_track_duration(track_key):
    return get_track_details(track_key)['duration_ms']


@lru_cache(maxsize=2**16)
def get_track_details(track_key):
  sp = get_spotify_api_client()

  track = sp.track(track_key)
  logger.info(track)
  return track


@cached(TTLCache(2**10, 300))
def get_user_details(user_id):
  sp = get_spotify_api_client()

  return sp.user(user_id)

