import datetime
import uuid

from dateutil import parser
import simplejson as json


class Party(object):
  def __init__(self):
    self.id = None
    self.name = "unnamed"
    self.playing_track_id = None
    self.playing_track_start_time = datetime.datetime.utcnow()
    self.users = []

  def get_player_state_payload(self):
    return {
      'type': 'player',
      'data': {
        'playing_track_id': self.playing_track_id,
        'playing_track_position': self.current_track_position,
        'playing_track_user_added': ''
      }
    }

  def broadcast_player_state(self, connection):
    connection.publish('sutrofm:broadcast:parties:%s' % self.id, json.dumps(self.get_player_state_payload()))

  @property
  def current_track_position(self):
    return (datetime.datetime.utcnow() - self.playing_track_start_time).seconds

  def play_track(self, track_id):
    self.playing_track_id = track_id
    self.playing_track_start_time = datetime.datetime.utcnow()

  @staticmethod
  def get(connection, id):
    data = connection.hgetall('parties:%s' % id)
    if data:
      output = Party()
      output.id = id
      output.name = data.get('name', 'No name')
      output.playing_track_id = data.get('playing_track_id', None)
      output.playing_track_start_time = parser.parse(
        data.get('playing_track_start_time', datetime.datetime.utcnow().isoformat()))

      # Get users
      user_keys = connection.smembers('parties:%s:users' % id)
      output.users = [
        User.get(connection, key) for key in user_keys
      ]
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
      "playing_track_id": self.playing_track_id,
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

    connection.transaction(_save_users, 'parties:%s:users' % self.id)

    connection.sadd('parties', self.id)

  def add_user(self, user):
    if user not in self.users:
      self.users.append(user)

  def remove_user(self, user):
    if user in self.users:
      self.users.remove(user)


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

