import logging
import threading

# from django.conf import settings
from django.contrib.auth import logout
from django.core.management import call_command
from django.shortcuts import redirect, render
#
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


def make_party_manager(party_name):
  logger.debug('Spawning party manager %s' % party_name)
  party_manager_thread = threading.Thread(target=call_command, args=('party_manager', party_name))
  party_manager_thread.start()


def party(request, party_name):
  if not party_name:
    return redirect('party', party_name='rdio')

  party, created = Party.objects.get_or_create(name=party_name)
  request.user.check_in_to_party(party)

  context = {
    'party': party,
#     'initial_player_state_json': json.dumps(party.get_player_state_payload()),
#     'initial_queue_state_json': json.dumps(party.get_queue_state_payload()),
#     'initial_user_list_state_json': json.dumps(party.get_user_list_state_payload()),
#     'initial_messages_state_json': json.dumps(party.get_messages_state_payload(connection)),
#     'initial_theme_state_json': json.dumps(party.get_theme_state_payload()),
  }
  make_party_manager(party.name)
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
