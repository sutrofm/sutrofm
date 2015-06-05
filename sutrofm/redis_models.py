

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
        user_keys = connection.smembers('party:users:%s' % id)
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
    if not hasattr(self, 'id'):
      self.id = connection.scard('parties')+1
    connection.hmset("parties:%s" % self.id, {
      "name": self.name,
      "playingTrackPosition": self.playingTrackPosition,
      "playingTrackId": self.playingTrackId
    })
    # Save users
    for user in self.users:
        connection.sadd('party:users:%s' % self.id, user.id)
    connection.sadd('parties', self.id)

  def add_user(self, user):
    if user not in self.users:
        self.users.append(user)

  def remove_user(self, user):
    if user in self.users:
      self.users.remove(user)

class User(object):
    @staticmethod
    def get(connection, id):
        data = connection.hgetall('users:%s' % id)
        output = User()
        output.id = id
        output.displayName = data.get('displayName', '')
        output.iconUrl = data.get('iconUrl', '')
        output.userUrl = data.get('userUrl', '')
        output.rdioKey = data.get('rdioKey', '')
        return output

    @staticmethod
    def getall(connection):
      ids = connection.smembers('users')
      return [
        User.get(connection, i) for i in ids
      ]

    def save(self, connection):
      if not hasattr(self, 'id'):
        self.id = connection.scard('users') + 1
      connection.hmset("users:%s" % self.id, {
        "displayName": self.displayName,
        "iconUrl": self.iconUrl,
        "userUrl": self.userUrl,
        "rdioKey": self.rdioKey
      })
      connection.sadd('users', self.id)

