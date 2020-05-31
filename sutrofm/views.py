import logging
import json

from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.http import HttpResponseNotAllowed
from social_django.utils import load_strategy

from sutrofm.models import Party
from sutrofm.party_manager_utils import party_needs_new_manager, spawn_new_party_manager
from sutrofm.user_presence import refresh_user_presence

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


@login_required
def create_party(request):
  # TODO: a route to create parties already exists in the DRF native views, fold this into that
  if request.method == "POST":
      party_name = request.POST['room_name']
      party = Party.objects.create(name=party_name)
      spawn_new_party_manager(party.id)
      return redirect('party', party.id)
  else:
      return HttpResponseNotAllowed(["POST"])


@login_required
def party(request, party_id):
  party = Party.objects.get(id=party_id)
  refresh_user_presence(party_id, request.user.id)

  social = request.user.social_auth.get(provider='spotify')

  if party_needs_new_manager(party_id):
    spawn_new_party_manager(party_id)

  context = {
    'party': party,
    'room_id': party_id,
    'initial_player_state_json': json.dumps(party.get_player_state_payload()),
    'initial_queue_state_json': json.dumps(party.get_queue_state_payload()),
    'initial_user_list_state_json': json.dumps(party.get_user_list_state_payload()),
    'initial_messages_state_json': json.dumps(party.get_messages_state_payload()),
    'spotify_access_token': social.get_access_token(load_strategy()),
    'initial_theme_state_json': json.dumps(party.get_theme_state_payload()),
  }
  return render(request, 'party.html', context)


@login_required
def parties(request):
  context = {
    'body_class': 'parties'
  }
  return render(request, 'partylist.html', context)


@login_required
def player_helper(request):
  return render(request, 'player-helper.html')
