import logging
import json

from django.contrib.auth import logout
from django.shortcuts import redirect, render
from django.http import HttpResponseNotAllowed
from social_django.utils import load_strategy

from sutrofm.models import Party

logger = logging.getLogger(__name__)

def home(request):
  context = {
    # Something good
    'body_class': 'home'
  }
  return render(request, 'index.html', context)


def logout_view(request):
  logout(request)
  return redirect('index')


def create_party(request):
  # TODO: a route to create parties already exists in the DRF native views, fold this into that
  if request.method == "POST":
      party_name = request.POST['room_name']
      party = Party.objects.create(name=party_name)
      party.spawn_new_manager()
      return redirect('party', party.id)
  else:
      return HttpResponseNotAllowed(["POST"])


def party(request, party_id):
  party = Party.objects.get(id=party_id)
  request.user.check_in_to_party(party)

  social = request.user.social_auth.get(provider='spotify')

  if party.needs_new_manager():
    party.spawn_new_manager()

  context = {
    'party': party,
    'room_id': party_id,
    'initial_player_state_json': json.dumps(party.get_player_state_payload()),
    'initial_queue_state_json': json.dumps(party.get_queue_state_payload()),
    'initial_user_list_state_json': json.dumps(party.get_user_list_state_payload()),
    'initial_messages_state_json': json.dumps(party.get_messages_state_payload()),
    'spotify_access_token': social.get_access_token(load_strategy())
#     'initial_theme_state_json': json.dumps(party.get_theme_state_payload()),
  }
  return render(request, 'party.html', context)
#
#
def parties(request):
  context = {
    'body_class': 'parties'
  }
  return render(request, 'partylist.html', context)
#
#
def player_helper(request):
  return render(request, 'player-helper.html')
