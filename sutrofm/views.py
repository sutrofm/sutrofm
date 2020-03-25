import uuid

from django.shortcuts import redirect, render

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
  }
  make_room_daemon(room_name)
  return render(request, 'party.html', context)


def parties(request):
  context = {
    'body_class': 'parties'
  }
  return render(request, 'partylist.html', context)


