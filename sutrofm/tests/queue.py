import datetime
import json
import uuid

from django.conf import settings
from django.test import TestCase, Client
from redis import ConnectionPool, StrictRedis

from sutrofm.redis_models import Party, User, QueueEntry


class QueueTestCase(TestCase):
    def setUp(self):
        redis_connection_pool = ConnectionPool(**settings.WS4REDIS_CONNECTION)
        self.redis = StrictRedis(connection_pool=redis_connection_pool)

        # Create the party
        self.party = Party()
        self.party.name = 'party_name'
        self.party.id = 'party_id'
        self.party.save(self.redis)

        self.user = User()
        self.user.id = 'user_id'
        self.user.display_name = 'a display name'
        self.user.save(self.redis)

        self.user2 = User()
        self.user2.id = 'user_id2'
        self.user2.display_name = 'another display name'
        self.user2.save(self.redis)

    def tearDown(self):
        self.redis.flushdb()

    def test_create_queue_entry(self):
        """ Can we enqueue and save a song on a queue? """
        self.party.enqueue_song(self.user, 't112233')
        self.party.save(self.redis)
        p = Party.get(self.redis, self.party.id)
        self.assertEquals(p.queue[0].track_key, 't112233')

    def test_queue_ordering(self):
        """ Does the comparator on our QueueEntry work as expected? """
        q1 = QueueEntry()
        q1.timestamp = datetime.datetime(1950, 1, 1)

        q2 = QueueEntry()
        q2.timestamp = datetime.datetime(1960, 1, 1)

        queue = [q2, q1]

        q1.upvote(self.user)

        # More votes > fewer votes
        queue.sort()
        self.assertEquals(queue, [q1, q2])
        q1.downvote(self.user)
        queue.sort()
        self.assertEquals(queue, [q2, q1])

        # Timestamp priority if equal
        q2.downvote(self.user)
        queue.sort()
        self.assertEquals(queue, [q1, q2])

        # Multiple users voting
        q1.upvote(self.user)
        q2.upvote(self.user)
        q2.upvote(self.user2)
        queue.sort()
        self.assertEquals(queue, [q2, q1])

    def test_queue_remove(self):
        """ Do we dequeue the right song from the party? Does that song get properly removed? """
        q1 = self.party.enqueue_song(self.user, 't123')
        q2 = self.party.enqueue_song(self.user, 't456')
        q2.upvote(self.user2)
        next_entry = self.party.dequeue_next_song()
        self.assertEquals(next_entry, q2)
        self.party.save(self.redis)
        p = Party.get(self.redis, self.party.id)
        self.assertEquals(p.queue[0].id, q1.id)
