import random
import string
import uuid

from django.conf import settings
from django.test import TestCase, Client
from redis import ConnectionPool, StrictRedis

from sutrofm.redis_models import Party, User


class SutroTestCase(TestCase):
    def setUp(self):
        redis_connection_pool = ConnectionPool(**settings.WS4REDIS_CONNECTION)
        self.redis = StrictRedis(connection_pool=redis_connection_pool)
        self.client = Client()

    def tearDown(self):
        self.redis.flushdb()

    def random_string(self, length=None, str_type=None):
        DEFAULT_LENGTH = 10
        length = length if length else DEFAULT_LENGTH
        if str_type == 'number':
            string_type = string.digits
        else:
            string_type = string.lowercase
        return ''.join(random.choice(string_type) for x in range(length))

    def create_a_user(self, display_name, user_id=None, icon_url=None, user_url=None, rdio_key=None):
        user = User()
        user.display_name = display_name
        user.id = user_id if user_id else uuid.uuid4().hex
        user.icon_url = icon_url if icon_url else 'http://' + self.random_string() + '.jpg'
        user.user_url = user_url if user_url else 'http://' + self.random_string() + '.com/' + self.random_string()
        user.rdio_key = rdio_key if rdio_key else 's' + self.random_string(length=5, str_type='number')
        user.save(self.redis)
        return user

    def create_a_party(self, party_id, name):
        party = Party()
        party.id = party_id
        party.name = name
        party.save(self.redis)
        return party