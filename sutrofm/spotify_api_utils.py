import logging

import spotipy

from sutrofm import settings


logger = logging.getLogger(__name__)


def get_track_duration(track_key):
    return get_track_details(track_key)['duration_ms']


def get_track_details(track_key):
  client_credentials_manager = spotipy.SpotifyClientCredentials(client_id=settings.SOCIAL_AUTH_SPOTIFY_KEY,
                                                                client_secret=settings.SOCIAL_AUTH_SPOTIFY_SECRET)
  sp = spotipy.Spotify(client_credentials_manager=client_credentials_manager)

  track = sp.track(track_key)
  logger.info(track)
  return track
