import datetime

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
