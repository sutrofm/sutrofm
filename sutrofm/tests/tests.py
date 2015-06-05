import json
from django.conf import settings
from django.test import TestCase, Client
from redis import ConnectionPool, StrictRedis
from sutrofm.redis_models import Party


class PartiesTestCase(TestCase):
  def setUp(self):
    redis_connection_pool = ConnectionPool(**settings.WS4REDIS_CONNECTION)
    self.redis = StrictRedis(connection_pool=redis_connection_pool)

  def tearDown(self):
    self.redis.flushall()

  def test_returns_empty_list_of_parties(self):
    c = Client()
    response = c.get('/api/parties')
    self.assertJSONEqual(response.content, [])

  def test_returns_the_list_of_parties(self):

    party = Party()
    party.name = "party-lives-on"
    party.save(self.redis)
    c = Client()
    response = c.get('/api/parties')

    json_response = json.loads(response.content)

    self.assertIsInstance(json_response[0]['id'], unicode)
    self.assertEqual(len(json_response[0]['id']), 32)
    self.assertEqual(json_response[0]['name'], party.name)
    self.assertEqual(len(json_response[0]['people']), 0)

