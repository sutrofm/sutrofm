import calendar
import datetime
import time
import requests
import uuid
import random

from django.conf import settings

import simplejson as json
from dateutil import parser


ACTIVITY_EXPIRES = 5

def get_rdio_user_data(rdio_user_key):
  response = requests.post('https://services.rdio.com/api/1/get', {
    'keys': rdio_user_key,
    'method': 'get',
    'access_token': settings.RDIO_ACCESS_TOKEN
  })
  return json.loads(response.text)['result'][rdio_user_key]


def get_rdio_track_data(rdio_track_key):
  response = requests.post('https://services.rdio.com/api/1/get', {
    'keys': rdio_track_key,
    'method': 'get',
    'access_token': settings.RDIO_ACCESS_TOKEN
  })
  return json.loads(response.text)['result'][rdio_track_key]


class Party(object):

  def __init__(self):
    self.id = None
    self.name = "unnamed"
    self.playing_track_key = None
    self.playing_track_start_time = datetime.datetime.utcnow()
    self.playing_track_user_key = None
    self.theme = 'Click me to change the theme!'

    self._users = {}
    self.queue = []
    self.skippers = set()
    self.messages = []

  def add_message(self, message):
    self.messages.append(message)

  def active_users(self):
    return [user for user in self._users.values() if user.is_active(self.id)]

  def get_player_state_payload(self):
    return {
      'type': 'player',
      'data': {
        'playing_track_key': self.playing_track_key,
        'playing_track_position': self.current_track_position,
        'playing_track_user_key': self.playing_track_user_key
      }
    }

  def get_queue_state_payload(self):
    return {
      'type': 'queue',
      'data': self.queue_to_dict()
    }

  def get_user_list_state_payload(self):
    return {
      'type': 'user_list',
      'data': self.users_to_dict()
    }

  def get_messages_state_payload(self, redis):
    recent_messages = Message.get_recent(redis, self.id)
    return {
      'type': 'messages',
      'data': [
        message.to_dict() for message in recent_messages
      ]
    }

  def get_message_added_payload(self, message):
    return {
      'type': 'message_added',
      'data': message.to_dict()
    }

  def get_theme_state_payload(self):
    return {
      'type': 'theme',
      'data': self.theme_to_dict()
    }

  def theme_to_dict(self):
    return {
      'theme': self.theme
    }

  def broadcast_player_state(self, connection):
    connection.publish('sutrofm:broadcast:parties:%s' % self.id, json.dumps(self.get_player_state_payload()))

  def broadcast_queue_state(self, connection):
    connection.publish('sutrofm:broadcast:parties:%s' % self.id, json.dumps(self.get_queue_state_payload()))

  def broadcast_user_list_state(self, connection):
    connection.publish('sutrofm:broadcast:parties:%s' % self.id, json.dumps(self.get_user_list_state_payload()))

  def broadcast_messages_state(self, connection):
    connection.publish(
      'sutrofm:broadcast:parties:%s' % self.id,
      json.dumps(self.get_messages_state_payload(connection))
    )

  def broadcast_message_added(self, connection, message):
    connection.publish('sutrofm:broadcast:parties:%s' % self.id, json.dumps(self.get_message_added_payload(message)))

  def broadcast_theme_state(self, connection):
    connection.publish('sutrofm:broadcast:parties:%s' % self.id, json.dumps(self.get_theme_state_payload()))

  @property
  def current_track_position(self):
    return (datetime.datetime.utcnow() - self.playing_track_start_time).seconds

  def play_track(self, track_key, user):
    self.playing_track_key = track_key
    self.playing_track_start_time = datetime.datetime.utcnow()

  def skip_stop(self):
    self.playing_track_key = None
    self.playing_track_start_time = datetime.datetime.utcnow()
    self.playing_track_user_key = None

  def play_next_track(self):
    """ Dequeue the next song and play it """
    next_track_entry = self.dequeue_next_song()
    if next_track_entry:
      self.play_track(next_track_entry.track_key, next_track_entry.submitter)
    else:
      self.skip_stop()
    self.clear_skippers()

  def clear_skippers(self):
    """GILLIGANNNNNN!!!"""
    self.skippers = set()

  def vote_to_skip(self, user):
    self.skippers.add(user.id)

  def should_skip(self):
    return len(self.skippers) > (len(self.active_users()) / 2)

  @staticmethod
  def get(connection, id):
    data = connection.hgetall('parties:%s' % id)
    if data:
      output = Party()
      output.id = id
      output.name = data.get('name', 'No name')
      output.playing_track_key = data.get('playing_track_key', None)
      output.playing_track_start_time = parser.parse(
        data.get('playing_track_start_time', datetime.datetime.utcnow().isoformat()))
      output.playing_track_user_key = data.get('playing_track_user_key', None)

      # Get users
      user_keys = connection.smembers('parties:%s:users' % id)
      output._users = {
        key: User.get(connection, key) for key in user_keys
      }

      # Get queue
      queue_keys = connection.smembers('parties:%s:queue' % id)
      output.queue = [QueueEntry.get(connection, id, key) for key in queue_keys if key]

      # Get skippers
      skippers = data.get('skippers', None)
      output.skippers = set(skippers.split(',') if skippers else [])

      # Get theme
      output.theme = data.get('theme', '')

      return output
    else:
      return None

  @staticmethod
  def getall(connection):
    ids = connection.smembers('parties')
    return [
      Party.get(connection, i) for i in ids
    ]

  def save(self, connection):
    if not self.id:
      self.id = uuid.uuid4().hex
    connection.hmset("parties:%s" % self.id, {
      "name": self.name,
      "playing_track_key": self.playing_track_key or '',
      "playing_track_start_time": self.playing_track_start_time,
      "playing_track_user_key": self.playing_track_user_key,
      "skippers": ",".join(self.skippers),
      "theme": self.theme,
    })
    # Save users

    def _save_users(pipe):
      old_users = pipe.smembers('parties:%s:users' % self.id)
      for old_user_id in old_users:
        if old_user_id not in self._users:
          pipe.srem('parties:%s:users' % self.id, old_user_id)

      for user_id in self._users:
        pipe.sadd('parties:%s:users' % self.id, user_id)

    # Save queue
    def _save_queue(pipe):
      old_queue_entries = pipe.smembers('parties:%s:queue' % self.id)
      for old_queue_entry_id in old_queue_entries:
        if old_queue_entry_id not in self.queue:
          pipe.srem('parties:%s:queue' % self.id, old_queue_entry_id)

      for queue_entry in self.queue:
        queue_entry.save(pipe)
        pipe.sadd('parties:%s:queue' % self.id, queue_entry.id)

    connection.transaction(_save_users, 'parties:%s:users' % self.id)
    connection.transaction(_save_queue, 'parties:%s:queue' % self.id)

    connection.sadd('parties', self.id)

  def add_user(self, connection, user):
    should_save = user.id not in self._users
    self._users[user.id] = user
    user.visit_party(self.id)
    if should_save:
      self.save(connection)

  def enqueue_song(self, user, track_key):
    qe = QueueEntry()
    qe.track_key = track_key
    qe.submitter = user
    qe.party_id = self.id
    # Assume the queueing user wants to upvote their own song
    qe.upvote(user)
    self.queue.append(qe)
    return qe

  def remove_queue_entry(self, queue_entry):
    self.queue.remove(queue_entry)

  def dequeue_next_song(self):
    if self.queue:
      self.queue.sort(reverse=True)
      return self.queue.pop()
    else:
      return None

  def to_dict(self):
    return {
      "id": self.id,
      "name": self.name,
      "people": [user.to_dict() for user in self._users.values()],
      "player": {
        "playingTrack": {
          "trackKey": self.playing_track_key
        }
      }
    }

  def to_json(self):
    return json.dumps(self.to_dict())

  def get_queue_entry(self, queue_entry_id):
    for queue_entry in self.queue:
      if queue_entry.id == queue_entry_id:
        return queue_entry
    return None

  def queue_to_dict(self):
    return [
      {
        'queue_entry_id': entry.id,
        'track_key': entry.track_key,
        'submitter': entry.submitter.to_dict(),
        'upvotes': list(entry.upvotes),
        'downvotes': list(entry.downvotes),
        'timestamp': entry.timestamp.isoformat(),
      } for entry in self.queue
    ]

  def users_to_dict(self):
    return [
      user.to_dict() for user in self._users.values()
    ]

  def messages_to_dict(self):
    return [
      m.to_dict() for m in self.messages
    ]


class QueueEntry(object):
  def __init__(self):
    self.id = None
    self.upvotes = set() # Set of user ids
    self.downvotes = set() # Set of user ids
    self.track_key = ''
    self.submitter = None
    self.timestamp = datetime.datetime.utcnow()
    self.party_id = ''

  @staticmethod
  def get(connection, party_id, id):
    data = connection.hgetall('parties:%s:queue:%s' % (party_id, id))
    if data:
      output = QueueEntry()
      output.id = id
      output.party_id = party_id
      output.track_key = data.get('track_key', '')
      output.submitter = User.get(connection, data.get('submitter', ''))
      output.upvotes = data.get('upvotes', '').split(",")
      output.downvotes = data.get('downvotes', '').split(",")
      # Filter out empty strings
      output.upvotes = set(x for x in output.upvotes if x)
      output.downvotes = set(x for x in output.downvotes if x)
      output.timestamp = parser.parse(data.get('timestamp', datetime.datetime.utcnow().isoformat()))
      return output
    else:
      return None

  def save(self, connection):
    if not self.id:
      self.id = uuid.uuid4().hex
    connection.hmset('parties:%s:queue:%s' % (self.party_id, self.id), {
      'track_key': self.track_key,
      'submitter': self.submitter.id,
      'upvotes': ",".join((str(x) for x in self.upvotes if x)),
      'downvotes': ",".join((str(x) for x in self.downvotes if x)),
      'timestamp': self.timestamp.isoformat()
    })

  @property
  def score(self):
    return len(self.upvotes) - len(self.downvotes)

  def upvote(self, user):
    if user.id in self.downvotes:
      self.downvotes.remove(user.id)
    self.upvotes.add(user.id)

  def downvote(self, user):
    if user.id in self.upvotes:
      self.upvotes.remove(user.id)
    self.downvotes.add(user.id)

  def __cmp__(self, other):
    if isinstance(other, QueueEntry):
      if other.score == self.score:
        return cmp(self.timestamp, other.timestamp)
      return cmp(other.score, self.score)
    else:
      return -1

  def to_dict(self):
    queue_dict = {
      'track_key': self.track_key,
      'submitter': self.submitter.id,
      'upvotes': ",".join(self.upvotes),
      'downvotes': ",".join(self.downvotes),
      'timestamp': self.timestamp.isoformat()
    }
    return queue_dict

  def to_json(self):
    return json.dumps(self.to_dict())


class User(object):
  def __init__(self):
    self.id = None
    self.display_name = None
    self.icon_url = None
    self.user_url = None
    self.last_check_in = None
    self.party_id = None

  @property
  def active(self):
    return datetime.datetime.utcnow() - self.last_check_in > datetime.timedelta(minutes=5)

  @staticmethod
  def get(connection, id):
    data = connection.hgetall('users:%s' % id)
    if data:
      output = User()
      output.id = id
      output.display_name = data.get('display_name', '')
      output.icon_url = data.get('icon', '')
      output.user_url = data.get('user_url', '')
      output.last_check_in = parser.parse(data.get('last_check_in', datetime.datetime.utcnow().isoformat()))
      output.party_id = data.get('party_id', '')
      return output
    else:
      return None

  @staticmethod
  def getall(connection):
    ids = connection.smembers('users')
    return [
      User.get(connection, i) for i in ids
    ]

  @staticmethod
  def from_request(connection, request):
    uuid = request.session.get('uuid')
    user = User.get(connection, uuid)
    if not user:
      user = User()
      user.id = uuid
      user.last_check_in = datetime.datetime.utcnow()

      icons = [
        '/static/img/icons/husky.jpeg',
        '/static/img/icons/raccoon.jpeg',
        '/static/img/icons/glasses_cat.jpeg',
        '/static/img/icons/shepherd.jpeg',
        '/static/img/icons/rhino.jpeg',
      ]
      user.icon_url = random.choice(icons)
      user.display_name = request.session.get('display_name')

      user.save(connection)
    return user

  def checked_in_recently(self):
    return datetime.datetime.utcnow() - self.last_check_in <= datetime.timedelta(seconds=ACTIVITY_EXPIRES)

  def is_active(self, party_id):
    return self.party_id == party_id and self.checked_in_recently()

  def visit_party(self, party_id):
    self.party_id = party_id
    self.last_check_in = datetime.datetime.utcnow()

  def save(self, connection):
    if not self.id:
      self.id = connection.scard('users') + 1
    connection.hmset("users:%s" % self.id, {
      "display_name": self.display_name,
      "icon": self.icon_url,
      "user_url": self.user_url,
      "last_check_in": self.last_check_in,
      "party_id": self.party_id
    })
    connection.sadd('users', self.id)

  def to_dict(self):
    return {
      "id": self.id,
      "display_name": self.display_name,
      "icon": self.icon_url,
      "user_url": self.user_url,
      "last_check_in": self.last_check_in.isoformat(),
      "is_active": self.is_active(self.party_id),
      "party_id": self.party_id
    }

  def to_json(self):
    return json.dumps(self.to_dict())


class Message(object):
  def __init__(self):
    self.message_type = None
    self.timestamp = datetime.datetime.utcnow()

    # For type == 'chat'
    self.user_id = None
    self.text = None

    # For type == 'new_track'
    self.track_key = None
    self.track_title = None
    self.track_artist = None
    self.track_url = None
    self.icon_url = None

  @staticmethod
  def get_recent(connection, party_id, count=50):
    message_ids = connection.zrange('parties:%s:messages' % party_id, -count, -1)
    messages = [
      Message.get(connection, party_id, message_id) for message_id in message_ids
    ]
    return messages

  @staticmethod
  def make_now_playing_message(connection, party, track_key):
    output = Message.for_party(connection, party)
    output.message_type = 'new_track'
    output.track_key = track_key
    if track_key:
      track_info = get_rdio_track_data(track_key)
      output.track_title = track_info['name']
      output.track_artist = track_info['artist']
      output.track_url = 'http://rdio.com%s' % track_info['url']
      output.icon_url = track_info['dynamicIcon']
    return output

  @staticmethod
  def for_party(connection, party):
    m = Message()
    m.id = Message.get_next_message_id(connection, party)
    m.party_id = party.id
    return m

  @staticmethod
  def get_next_message_id(connection, party):
    return connection.incr('parties:%s:message_id' % party.id)

  @staticmethod
  def get(connection, party_id, message_id):
    schema = {
        'message_type': None,
        'text': None,
        'user_id': None,
        'track': None,
        'track_key': None,
        'track_title': None,
        'track_artist': None,
        'track_url': None,
        'icon_url': None,
        'timestamp': None,
    }
    data = {}
    values = connection.hmget('parties:%s:messages:%s' % (party_id, message_id), schema.keys())
    output = Message()
    output.id = message_id
    for index, key in enumerate(schema.keys()):
      data[key] = values[index]
      setattr(output, key, values[index])
    output.timestamp = parser.parse(data['timestamp']) if data['timestamp'] else datetime.datetime.utcnow()
    return output

  def save(self, connection):
    redis_dict = {k: v for k, v in self.to_dict().iteritems() if v is not None}
    # redis hmsets None as the string 'None', so delete those fields.
    delete_fields = [k for k, v in self.to_dict().iteritems() if v is None]
    connection.hdel('parties:%s:messages:%s' % (self.party_id, self.id), delete_fields)
    connection.hmset('parties:%s:messages:%s' % (self.party_id, self.id), redis_dict)
    connection.zadd('parties:%s:messages' % self.party_id, calendar.timegm(time.gmtime()), self.id)

  def to_dict(self):
    data = {
      'message_type': self.message_type,
      'timestamp': self.timestamp.isoformat(),
    }

    if (self.message_type == "chat"):
      data.update({
        'text': self.text,
        'user_id': self.user_id,
      })
    elif (self.message_type == "new_track"):
      data.update({
        'track_key': self.track_key,
        'track_title': self.track_title,
        'track_artist': self.track_artist,
        'track_url': self.track_url,
        'icon_url': self.icon_url
      })
    return data

  def to_json(self):
    return json.dumps(self.to_dict())
