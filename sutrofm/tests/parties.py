import json

from sutrofm.tests.sutro_test_case import SutroTestCase


class PartiesTestCase(SutroTestCase):
  def test_returns_empty_list_of_parties(self):
    response = self.client.get('/api/parties')
    self.assertJSONEqual(response.content, {'results':[]})

  def test_returns_list_of_parties(self):
    party = self.create_a_party('party-lives-on')
    user_shindiger = self.create_a_user('shindiger')
    user_bob = self.create_a_user('bob')
    party.add_user(user_shindiger)
    party.add_user(user_bob)
    party.save(self.redis)

    response = self.client.get('/api/parties')

    json_parties = json.loads(response.content)['results']

    self.assertIsInstance(json_parties[0]['id'], unicode)
    self.assertEqual(len(json_parties[0]['id']), 32)
    self.assertEqual(json_parties[0]['name'], party.name)
    self.assertEqual(len(json_parties[0]['people']), 2)

    for person in json_parties[0]['people']:
      self.assertIn(person['id'], [user_bob.id, user_shindiger.id])
      self.assertIn(person['displayName'], [user_bob.display_name, user_shindiger.display_name])

    party.remove_user(user_bob)
    party.save(self.redis)

    response = self.client.get('/api/parties')
    json_response = json.loads(response.content)
    self.assertEqual(len(json_response['results'][0]['people']), 1)





