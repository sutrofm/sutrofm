

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
      self.id = connection.scard('parties')+1
    connection.hmset("parties:%s" % self.id, {
      "name": self.name,
    })
    connection.sadd('parties', self.id)
