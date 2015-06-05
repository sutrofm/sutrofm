

class Party(object):
    @staticmethod
    def get(connection, id):
      data = connection.hgetall('parties:%s' % id)
      output = Party()
      output.id = id
      output.name = data.get('name', 'No name')
      return output

    @staticmethod
    def getall(connection):
      ids = connection.smembers('parties')
      return [
        Party.get(connection, i) for i in ids
      ]

    def save(self, connection):
      if not hasattr(self, 'id'):
        self.id = connection.scard('parties') + 1
      connection.hmset("parties:%s" % self.id, {
        "name": self.name,
      })
      connection.sadd('parties', self.id)

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

