import json

from sutrofm.tests.sutro_test_case import SutroTestCase


class UsersTestCase(SutroTestCase):
  def test_returns_empty_list_of_users(self):
    response = self.client.get('/api/users', follow=True)
    self.assertJSONEqual(response.content, {'results':[]})

  def test_returns_list_of_users(self):
      # Add dummy users
      users = [
      {
        'display_name': 'alice',
        'user_id': '1234',
        'icon_url': 'http://pictures.com/alice.jpg',
        'user_url': 'http://profiles.com/alice',
        'rdio_key': 's4321'
      },
      {
        'display_name': 'bob',
        'user_id': '2345',
        'icon_url': 'http://pictures.com/bob.jpg',
        'user_url': 'http://profiles.com/bob',
        'rdio_key': 's5432'
      }
      ]
      map(lambda x: self.create_a_user(x['display_name'],
       user_id=x['user_id'],
       icon_url=x['icon_url'],
       user_url=x['user_url'],
       rdio_key=x['rdio_key']), users)

      # Retrieve users via api and verify their attributes are as expected
      response = self.client.get('/api/users', follow=True)
      json_response = json.loads(response.content)
      json_users = json_response['results']

      for user in json_users:
        user_to_check = {
          'display_name': user.get('displayName'),
          'user_id': user.get('id'),
          'icon_url': user.get('iconUrl'),
          'user_url': user.get('userUrl'),
          'rdio_key': user.get('rdioKey')
        }
        self.assertTrue(user_to_check in users)

  def test_get_a_user_by_id(self):
    user = {
      'display_name': 'charlie',
      'user_id': '3456',
      'icon_url': 'http://pictures.com/charlie.jpg',
      'user_url': 'http://profiles.com/charlie',
      'rdio_key': 's3456'
    }
    user = self.create_a_user(
      display_name=user['display_name'],
      user_id=user['user_id'],
      icon_url=user['icon_url'],
      user_url=user['user_url'],
      rdio_key=user['rdio_key']
    )

    response = self.client.get('/api/user/%s' % user.id, follow=True)

    json_response = json.loads(response.content)
    json_user = json_response['results']

    self.assertEqual(json_user['id'], user.id)
    self.assertEqual(json_user['displayName'], user.display_name)
    self.assertEqual(json_user['iconUrl'], user.icon_url)
    self.assertEqual(json_user['userUrl'], user.user_url)
    self.assertEqual(json_user['rdioKey'], user.rdio_key)
