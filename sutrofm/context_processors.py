from django.conf import settings

from social_auth.models import UserSocialAuth
from firebase_token_generator import create_token


class RdioTokens(object):
  def __init__(self, rdio_oauth2):
    rdio_user_key = rdio_oauth2.extra_data['rdio_id']
    custom_data = {
      'rdio_user_key': rdio_user_key,
    }
    options = {
      'debug': settings.DEBUG,
    }
    firebase_token = create_token(settings.FIREBASE_TOKEN, custom_data, options)

    extra_data = rdio_oauth2.extra_data
    self.username = extra_data['rdio_username']
    self.stream_region = extra_data['rdio_stream_region']
    self.id = extra_data['rdio_id']
    self.icon_url = extra_data['rdio_icon_url']
    self.profile_url = 'http://rdio.com%s' % extra_data['rdio_profile_url']
    self.access_token = extra_data['access_token']
    self.refresh_token = extra_data['refresh_token']
    self.client_id = settings.RDIO_OAUTH2_KEY
    self.firebase_token = firebase_token


def rdio(request):
  if request.user.is_authenticated():
    try:
      rdio_auth = request.user.social_auth.filter(provider='rdio-oauth2').get()
      rdio = RdioTokens(rdio_auth)
    except UserSocialAuth.DoesNotExist:
      rdio = None
  else:
    rdio = None

  return {
    'rdio': rdio
  }
