import datetime
import uuid

from dateutil import parser
import simplejson as json


class Party(object):
  def __init__(self):
    self.id = None
    self.name = "unnamed"
    self.playing_track_key = None
    self.playing_track_start_time = datetime.datetime.utcnow()
    self.playing_track_user = None
    self.users = []
    self.queue = []

  def get_player_state_payload(self):
    return {
      'type': 'player',
      'data': {
        'playing_track_key': self.playing_track_key,
        'playing_track_position': self.current_track_position,
        'playing_track_user_added': ''
      }
    }

  def broadcast_player_state(self, connection):
    connection.publish('sutrofm:broadcast:parties:%s' % self.id, json.dumps(self.get_player_state_payload()))

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

  def should_skip(self):
    return False # TODO

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
      "playing_track_key": self.playing_track_key,
      "playing_track_start_time": self.playing_track_start_time,
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

    connection.transaction(_save_users, 'parties:%s:users' % self.id)
    connection.transaction(_save_queue, 'parties:%s:queue' % self.id)

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

  def dequeue_next_song(self):
    if self.queue:
      self.queue.sort(reverse=True)
      return self.queue.pop()
    else:
      return None

  def to_dict(self):
    party_dict = {
      'id': self.id,
      'name': self.name,
      'people': [{'id': user.id, 'displayName': user.display_name} for user in self.users],
      'player': {
        'playingTrack': {
          'trackKey': self.playing_track_key,
        },
      },
    }
    return party_dict

  def to_json(self):
    return json.dumps(self.to_dict())


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
      output.upvotes = set(data.get('upvotes', '').split(","))
      output.downvotes = set(data.get('upvotes', '').split(","))
      output.timestamp = parser.parse(data.get('timestmap', datetime.datetime.utcnow().isoformat()))
      return output
    else:
      return None

  def save(self, connection):
    if not self.id:
      self.id = uuid.uuid4().hex
    connection.hmset('parties:%s:queue:%s' % (self.party_id, self.id), {
      'track_key': self.track_key,
      'submitter': self.submitter.id,
      'upvotes': ",".join(self.upvotes),
      'downvotes': ",".join(self.downvotes),
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

  @staticmethod
  def get(connection, id):
    data = connection.hgetall('users:%s' % id)
    output = User()
    output.id = id
    output.display_name = data.get('displayName', '')
    output.icon_url = data.get('iconUrl', '')
    output.user_url = data.get('userUrl', '')
    output.rdio_key = data.get('rdioKey', '')
    return output

  @staticmethod
  def getall(connection):
    ids = connection.smembers('users')
    return [
      User.get(connection, i) for i in ids
    ]

  def save(self, connection):
    if not self.id:
      self.id = connection.scard('users') + 1
    connection.hmset("users:%s" % self.id, {
      "displayName": self.display_name,
      "iconUrl": self.icon_url,
      "userUrl": self.user_url,
      "rdioKey": self.rdio_key
    })
    connection.sadd('users', self.id)

  def to_dict(self):
    user_dict = {
      'id': self.id,
      'displayName': self.display_name,
      'iconUrl': self.icon_url,
      'userUrl': self.user_url,
      'rdioKey': self.rdio_key
    }
    return user_dict

  def to_json(self):
    return json.dumps(self.to_dict())


class Messages(object):
  @staticmethod
  def get_recent(connection, party_messages_id, count=50):
    messages = connection.lrange('messages:%s' % party_messages_id, 0, count)
    return messages

  def save_message(self, connection, message, message_type, user, party_id):
    if not hasattr(self, 'party_messages_id'):
      self.party_messages_id = party_id

    connection.lpush("messages:%s" % self.party_messages_id, {
      "message": message,
      "type": message_type,
      "user": user,
      "timestamp": datetime.datetime.utcnow()
    })

  def to_dict(self):
    message_dict = {
      'party_messages_id': self.party_messages_id,
      'message': self.message,
      'type': self.message_type,
      'user': self.user,
      'timestamp': self.timestamp
    }
    return message_dict

  def to_json(self):
    return json.dumps(self.to_dict())
