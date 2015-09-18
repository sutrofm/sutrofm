import subprocess
import os
import json
import psutil

from django.conf import settings
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render, render_to_response
from redis import ConnectionPool, StrictRedis

from sutrofm.redis_models import Party, User


redis_connection_pool = ConnectionPool(**settings.WS4REDIS_CONNECTION)


def home(request):
  context = {
    # Something good
    'body_class': 'home'
  }
  return render(request, 'index.html', context)


def make_room_daemon(room_name):
  child_processes = psutil.Process(os.getpid()).get_children()
  for process in child_processes:
    try:
      if process.cmdline() and len(process.cmdline()) > 0 and process.cmdline()[-1] == room_name:
        return
    except psutil.AccessDenied:
      pass
  directory = os.path.dirname(os.path.realpath(__file__))
  subprocess.Popen(["python", "%s/../manage.py" % directory, "master", room_name])


@login_required
def party(request, room_name):
  if room_name is None:
    return redirect('/p/rdio')

  connection = StrictRedis(connection_pool=redis_connection_pool)
  party = Party.get(connection, room_name)
  if not party:
    party = Party()
    party.id = room_name
    party.name = room_name
    party.save(connection)

  user = User.from_request(connection, request)
  party.add_user(user)
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
    'initial_theme_state_json': json.dumps(party.get_theme_state_payload())
  }
  make_room_daemon(room_name)
  return render(request, 'party.html', context)


def parties(request):
  context = {
    'body_class': 'parties'
  }
  return render(request, 'partylist.html', context)


def sign_out(request):
  logout(request)
  return redirect('/')


def player_helper(request):
  return render_to_response('player-helper.html')
