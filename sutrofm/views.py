import subprocess
import os
import json
import psutil

from django.conf import settings
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import redirect, render, render_to_response
from firebase_token_generator import create_token
from redis import ConnectionPool, StrictRedis

from sutrofm.redis_models import Party


redis_connection_pool = ConnectionPool(**settings.WS4REDIS_CONNECTION)


def home(request):
  context = {
    # Something good
    'body_class': 'home'
  }
  return render(request, 'index.html', context)


def createauthtoken(request):
  rdio_user_key = request.GET.get('userKey')
  if rdio_user_key:
    custom_data = {'rdio_user_key': rdio_user_key}
    options = {'debug': settings.DEBUG}
    firebase_token = create_token(settings.FIREBASE_TOKEN, custom_data, options)
    response = {"token": firebase_token}
  else:
    response = {"error": "userKey is a required GET param"}

  return HttpResponse(json.dumps(response), content_type="application/json")


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

  context = {
    'firebase_url': "%s/%s" % (settings.FIREBASE_URL, room_name),
    'room_name': room_name,
    'body_class': 'party',
    'room_id': room_name,
    'initial_player_state_json': json.dumps(party.get_player_state_payload())
  }
  make_room_daemon(room_name)
  return render(request, 'party.html', context)


def parties(request):
  context = {
    'firebase_url': "%s/" % (settings.FIREBASE_URL,),
    'body_class': 'parties'
  }
  return render(request, 'partylist.html', context)


def sign_out(request):
  logout(request)
  return redirect('/')


def player_helper(request):
  return render_to_response('player-helper.html')
