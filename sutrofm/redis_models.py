import calendar
import datetime
import time
import uuid

from dateutil import parser
import simplejson as json
from sutrofm.context_processors import rdio



class Party(object):
  def __init__(self):
    self.id = None
    self.name = "unnamed"
    self.playing_track_key = None
    self.playing_track_start_time = datetime.datetime.utcnow()
    self.playing_track_user = None
    self.users = []
    self.queue = []
    self.skippers = []
    self.messages = []

  def add_message(self, message):
    self.messages.append(message)

  def get_player_state_payload(self):
    return {
      'type': 'player',
      'data': {
        'playing_track_key': self.playing_track_key,
        'playing_track_position': self.current_track_position,
        'playing_track_user_added': ''
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

  def broadcast_player_state(self, connection):
    connection.publish('sutrofm:broadcast:parties:%s' % self.id, json.dumps(self.get_player_state_payload()))

  def broadcast_queue_state(self, connection):
    connection.publish('sutrofm:broadcast:parties:%s' % self.id, json.dumps(self.get_queue_state_payload()))

  def broadcast_user_list_state(self, connection):
    connection.publish('sutrofm:broadcast:parties:%s' % self.id, json.dumps(self.get_user_list_state_payload()))

  @property
  def current_track_position(self):
    return (datetime.datetime.utcnow() - self.playing_track_start_time).seconds

  def play_track(self, track_key, user):
    self.playing_track_key = track_key
    self.playing_track_start_time = datetime.datetime.utcnow()
    self.playing_track_user = user

  def play_next_track(self):
    """ Dequeue the next song and play it """
    next_track_entry = self.dequeue_next_song()
    if next_track_entry:
      self.play_track(next_track_entry.track_key, next_track_entry.submitter)
    else:
      self.play_track(None, None)

  def clear_skippers(self):
    self.skippers = []

  def vote_to_skip(self, user):
    if user.id not in self.skippers:
      self.skippers.append(user.id)

  def should_skip(self):
    # return len(self.skippers) > len(self.users) / 2
    return False

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

      # Get users
      user_keys = connection.smembers('parties:%s:users' % id)
      output.users = [
        User.get(connection, key) for key in user_keys
      ]

      # Get queue
      queue_keys = connection.smembers('parties:%s:queue' % id)
      output.queue = filter(None, [
        QueueEntry.get(connection, id, key) for key in queue_keys
      ])

      # Get skippers
      output.skippers = data.get('skippers', '').split(',')
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
      "skippers": ",".join(self.skippers)
    })
    # Save users
    def _save_users(pipe):
      old_users = pipe.smembers('parties:%s:users' % self.id)
      for old_user_id in old_users:
        if old_user_id not in self.users:
          pipe.srem('parties:%s:users' % self.id, old_user_id)

      for user in self.users:
        pipe.sadd('parties:%s:users' % self.id, user.id)

    # Save queue
    def _save_queue(pipe):
      old_queue_entries = pipe.smembers('parties:%s:queue' % self.id)
      for old_queue_entry_id in old_queue_entries:
        if old_queue_entry_id not in self.queue:
          pipe.srem('parties:%s:queue' % self.id, old_queue_entry_id)

      for queue_entry in self.queue:
        queue_entry.save(pipe)
        pipe.sadd('parties:%s:queue' % self.id, queue_entry.id)

    # Save messages
    def _save_messages(pipe):
      for message in self.messages:
        pipe.zadd('parties:%s:messages' % self.id, calendar.timegm(time.gmtime()), message.id)

    connection.transaction(_save_users, 'parties:%s:users' % self.id)
    connection.transaction(_save_queue, 'parties:%s:queue' % self.id)
    connection.transaction(_save_messages, 'parties:%s:messages' % self.id)

    connection.sadd('parties', self.id)

  def add_user(self, user):
    if user not in self.users:
      self.users.append(user)

  def remove_user(self, user):
    if user in self.users:
      self.users.remove(user)

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
      "people": [{'id': user.id, 'displayName': user.display_name} for user in self.users],
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
            'queueEntryId': entry.id,
            'trackKey': entry.track_key,
            'submitter': entry.submitter.to_dict(),
            'upvotes': list(entry.upvotes),
            'downvotes': list(entry.downvotes),
            'timestamp': entry.timestamp.isoformat(),
            'userKey': entry.submitter.rdio_key
        } for entry in self.queue
    ]

  def users_to_dict(self):
    return [
      user.to_dict() for user in self.users
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
      output.upvotes = set(filter(None, output.upvotes))
      output.downvotes = set(filter(None, output.downvotes))
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
      'upvotes': ",".join(map(str, self.upvotes)),
      'downvotes': ",".join(map(str, self.downvotes)),
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
      'timestamp': self.timestamp
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
    self.rdio_key = None
    self.last_check_in = None

  @property
  def active(self):
    return  datetime.datetime.utcnow() - self.last_check_in > datetime.timedelta(minutes=5)

  @staticmethod
  def get(connection, id):
    data = connection.hgetall('users:%s' % id)
    if data:
      output = User()
      output.id = id
      output.display_name = data.get('displayName', '')
      output.icon_url = data.get('iconUrl', '')
      output.user_url = data.get('userUrl', '')
      output.rdio_key = data.get('rdioKey', '')
      output.last_check_in = parser.parse(data.get('lastCheckIn', datetime.datetime.utcnow().isoformat()))
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
    rdio_token = rdio(request)['rdio']
    user = User.get(connection, rdio_token.id)
    if not user:
      user = User()
      user.id = rdio_token.id
      user.display_name = rdio_token.username
      user.rdio_key = rdio_token.id
      user.last_check_in = datetime.datetime.utcnow()
      user.save(connection)
    return user

  def save(self, connection):
    if not self.id:
      self.id = connection.scard('users') + 1
    connection.hmset("users:%s" % self.id, {
      "displayName": self.display_name,
      "iconUrl": self.icon_url,
      "userUrl": self.user_url,
      "rdioKey": self.rdio_key,
      "lastCheckIn": self.last_check_in,
    })
    connection.sadd('users', self.id)

  def to_dict(self):
    return {
      "id": self.id,
      "fullName": self.display_name,
      "icon": self.icon_url,
      "userUrl": self.user_url,
      "rdioKey": self.rdio_key,
      "lastCheckIn": self.last_check_in.isoformat(),
      "isOnline": True
    }

  def to_json(self):
    return json.dumps(self.to_dict())


class Message(object):
  def __init__(self):
    self.message_type = None
    self.text = None
    self.user_key = None
    self.track = None
    self.timestamp = datetime.datetime.utcnow()

  @staticmethod
  def get_recent(connection, party_id, count=50):
    message_ids = connection.zrange('parties:%s:messages' % party_id, 0, count)
    messages = [
        Message.get(connection, party_id, message_id) for message_id in message_ids
    ]
    return messages

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
        'user': None,
        'track': None,
        'timestamp': None
    }
    data = {}
    values = connection.hmget('parties:%s:messages:%s' % (party_id, message_id), schema.keys())
    for index, key in enumerate(schema.keys()):
        data[key] = values[index]
    print data
    output = Message()
    output.id = message_id
    output.message_type = data['message_type']
    output.text = data['text']
    output.user_key = data['user']
    output.track = data['track']
    output.timestamp = data['timestamp']
    return output

  def save(self, connection):
    connection.hmset('parties:%s:messages:%s' % (self.party_id, self.id), self.to_dict())

  def to_dict(self):
    return {
      'message_type': self.message_type,
      'text': self.text,
      'user': self.user_key,
      'track': self.track,
      'timestamp': self.timestamp
    }

  def to_json(self):
    return json.dumps(self.to_dict())
