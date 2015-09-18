import json

from sutrofm.tests.sutro_test_case import SutroTestCase


class PartiesTestCase(SutroTestCase):
  def test_returns_empty_list_of_parties(self):
    response = self.client.get('/api/parties', follow=True)
    self.assertJSONEqual(response.content, {'results':[]})

  def test_returns_list_of_parties(self):
    party = self.create_a_party('party-lives-on', 'Party lives on!')
    user_shindiger = self.create_a_user('shindiger')
    user_bob = self.create_a_user('bob')
    party.add_user(user_shindiger)
    party.add_user(user_bob)
    party.save(self.redis)
    response = self.client.get('/api/parties', follow=True)

    json_response = json.loads(response.content)
    json_parties = json_response['results']

    response = self.client.get('/api/parties', follow=True)

    json_response = json.loads(response.content)
    json_parties = json_response['results']

    self.assertEqual(json_parties[0]['id'], party.id)
    self.assertEqual(json_parties[0]['name'], party.name)
    self.assertEqual(len(json_parties[0]['people']), 2)

    for person in json_parties[0]['people']:
      self.assertIn(person['id'], [user_bob.id, user_shindiger.id])
      self.assertIn(person['display_name'], [user_bob.display_name, user_shindiger.display_name])

    party.remove_user(user_bob)
    party.save(self.redis)

    response = self.client.get('/api/parties', follow=True)
    json_response = json.loads(response.content)
    self.assertEqual(len(json_response['results'][0]['people']), 1)

  def test_get_a_party_by_id(self):
    party = self.create_a_party('party-lives-on', 'Party lives one!')
    user_shindiger = self.create_a_user('shindiger')
    user_bob = self.create_a_user('bob')
    party.add_user(user_shindiger)
    party.add_user(user_bob)
    party.save(self.redis)

    response = self.client.get('/api/party/%s' % party.id, follow=True)

    json_response = json.loads(response.content)
    json_party = json_response['results']

    self.assertEqual(json_party['id'], party.id)
    self.assertEqual(json_party['name'], party.name)
    self.assertEqual(len(json_party['people']), 2)

  def test_skippers(self):
    party = self.create_a_party('party-lives-on', 'Party lives one!')
    user_shindiger = self.create_a_user('shindiger')
    user_bob = self.create_a_user('bob')
    user_sally = self.create_a_user('sally')
    party.add_user(user_shindiger)
    party.add_user(user_bob)
    party.add_user(user_sally)
    party.save(self.redis)

    self.assertFalse(party.should_skip())

    party.vote_to_skip(user_bob)
    self.assertFalse(party.should_skip())

    party.vote_to_skip(user_bob)
    self.assertFalse(party.should_skip())

    party.vote_to_skip(user_sally)
    self.assertTrue(party.should_skip())
