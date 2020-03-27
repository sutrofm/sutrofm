import json
import logging
import threading
import uuid

from django.conf import settings
from django.contrib.auth import logout
from django.core.management import call_command
from redis import ConnectionPool, StrictRedis
from django.shortcuts import redirect, render

from sutrofm.redis_models import Party, User

logger = logging.getLogger(__name__)

redis_connection_pool = ConnectionPool(**settings.WS4REDIS_CONNECTION)


def home(request):
  context = {
    # Something good
    'body_class': 'home'
  }
  return render(request, 'index.html', context)


# Add some display name information and assign a UUID before continuing
def login(request):
  name = request.POST["name"]
  request.session['display_name'] = name
  request.session['uuid'] = str(uuid.uuid4())
  return redirect('parties')


def logout_view(request):
  logout(request)
  return redirect('/')


def make_room_daemon(room_name):
  logger.debug('Spawning room daemon %s' % room_name)
  room_thread = threading.Thread(target=call_command, args=('master', room_name))
  room_thread.start()


def party(request, room_name):
  if room_name is None:
    return redirect('/p/rdio')

  connection = StrictRedis(connection_pool=redis_connection_pool)
  party = Party.get(connection, room_name)
  if not party:
    party = Party()
    party.id = room_name
    party.name = room_name
    party.playing_track_user_key = request.user.social_auth.get(provider='spotify').uid
    party.save(connection)

  user = User.from_request(connection, request)
  party.add_user(connection, user)
  party.broadcast_user_list_state(connection)
  party.save(connection)

  context = {
    'room_name': room_name,
    'body_class': 'party',
    'room_id': room_name,
    'initial_player_state_json': json.dumps(party.get_player_state_payload()),
    'initial_queue_state_json': json.dumps(party.get_queue_state_payload()),
    'initial_user_list_state_json': json.dumps(party.get_user_list_state_payload()),
    'initial_messages_state_json': json.dumps(party.get_messages_state_payload(connection)),
    'initial_theme_state_json': json.dumps(party.get_theme_state_payload()),
    'current_user': json.dumps(user.to_dict()),
    'websocket_url': settings.WEBSOCKET_URL,
    'ws4redis_heartbeat': settings.WS4REDIS_HEARTBEAT
  }
  make_room_daemon(room_name)
  return render(request, 'party.html', context)


def parties(request):
  context = {
    'body_class': 'parties'
  }
  return render(request, 'partylist.html', context)


def player_helper(request):
  return render(request, 'player-helper.html')
