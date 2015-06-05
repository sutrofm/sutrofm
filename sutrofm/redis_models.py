import uuid


class Party(object):
  def __init__(self):
    self.id = None
    self.name = "unnamed"
    self.playingTrackId = None
    self.playingTrackPosition = 0
    self.users = []

  @staticmethod
  def get(connection, id):
    data = connection.hgetall('parties:%s' % id)
    if data:
      output = Party()
      output.id = id
      output.name = data.get('name', 'No name')
      output.playingTrackId = data.get('playingTrackId', None)
      output.playingTrackPosition = data.get('playingTrackId', 0)

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
      "playingTrackPosition": self.playingTrackPosition,
      "playingTrackId": self.playingTrackId
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

