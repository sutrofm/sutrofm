import datetime

from sutrofm.redis_models import Party, QueueEntry
from sutrofm.tests.sutro_test_case import SutroTestCase


class QueueTestCase(SutroTestCase):
    def setUp(self):
        super(QueueTestCase, self).setUp()

        self.party = self.create_a_party('party_id', 'party_name')
        self.user = self.create_a_user('a display name', user_id='user_id')
        self.user2 = self.create_a_user('another display name', user_id='user_id2')

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
