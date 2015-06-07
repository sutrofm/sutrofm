import json
import uuid

from django.conf import settings
from django.test import TestCase, Client
from redis import ConnectionPool, StrictRedis

from sutrofm.redis_models import Party, User


class PartiesTestCase(TestCase):
  def setUp(self):
    redis_connection_pool = ConnectionPool(**settings.WS4REDIS_CONNECTION)
    self.redis = StrictRedis(connection_pool=redis_connection_pool)

  def tearDown(self):
    self.redis.flushdb()

  def create_a_user(self, display_name):
    user = User()
    user.id = uuid.uuid4().hex
    user.display_name = display_name
    user.save(self.redis)
    return user

  def test_returns_empty_list_of_parties(self):
    c = Client()
    response = c.get('/api/parties', follow=True)
    self.assertJSONEqual(response.content, {'results': []})

  def create_a_party(self, party_id, name):
    party = Party()
    party.name = name
    party.save(self.redis)
    return party

  def test_returns_the_list_of_parties(self):
    party = self.create_a_party('party-lives-on', 'Party lives one!')
    user_shindiger = self.create_a_user('shindiger')
    user_bob = self.create_a_user('bob')
    party.add_user(user_shindiger)
    party.add_user(user_bob)
    party.save(self.redis)

    c = Client()
    response = c.get('/api/parties', follow=True)

    json_response = json.loads(response.content)
    json_parties = json_response['results']

    self.assertEqual(json_parties[0]['id'], party.id)
    self.assertEqual(json_parties[0]['name'], party.name)
    self.assertEqual(len(json_parties[0]['people']), 2)


    for person in json_parties[0]['people']:
      self.assertIn(person['id'], [user_bob.id, user_shindiger.id])
      self.assertIn(person['displayName'], [user_bob.display_name, user_shindiger.display_name])

    party.remove_user(user_bob)
    party.save(self.redis)

    response = c.get('/api/parties', follow=True)
    json_response = json.loads(response.content)
    self.assertEqual(len(json_response['results'][0]['people']), 1)

  def test_get_a_party_by_id(self):
    party = self.create_a_party('party-lives-on', 'Party lives one!')
    user_shindiger = self.create_a_user('shindiger')
    user_bob = self.create_a_user('bob')
    party.add_user(user_shindiger)
    party.add_user(user_bob)
    party.save(self.redis)

    c = Client()
    response = c.get('/api/parties/%s' % party.id, follow=True)

    json_response = json.loads(response.content)

    self.assertEqual(json_response['id'], party.id)
    self.assertEqual(json_response['name'], party.name)
    self.assertEqual(len(json_response['people']), 2)




