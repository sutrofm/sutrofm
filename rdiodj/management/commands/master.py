from collections import defaultdict
from datetime import datetime, timedelta
from django.core.management.base import BaseCommand
from django.conf import settings
from rdioapi import Rdio
import firebase
import logging
import time
from dateutil import parser

RDIO_OAUTH2_KEY='c2y48bscf6hpd768b6cwvafy'
RDIO_OAUTH2_SECRET='sHf9GavUrP'

WAIT_FOR_USERS = timedelta(minutes=5)


class Command(BaseCommand):
    def handle(self, room_name, *args, **kwargs):
        self.firebase = firebase.FirebaseApplication(settings.FIREBASE_URL)
        auth = firebase.FirebaseAuthentication(settings.FIREBASE_TOKEN, 'mkapolk@gmail.com')
        self.firebase.authentication = auth
        self.rdio = Rdio(RDIO_OAUTH2_KEY, RDIO_OAUTH2_SECRET, {})
        self.party_name = room_name
        self.party_data = self.get_party_data()
        self.currently_playing = None
        self.last_saw_users = datetime.now()

        self.currently_playing = None
        if 'player' in self.party_data and 'playingTrack' in self.party_data['player']:
            track_key = self.party_data['player']['playingTrack']['trackKey']
            self.current_track_duration = self.rdio.get(keys=track_key)[track_key]['duration']
            self.current_start_time = datetime.now() - timedelta(seconds=self.party_data['player']['position'])
        else:
            self.current_track_duration = None
            self.current_start_time = None

        self.run()

    def get_party_data(self):
        pd = defaultdict(lambda: defaultdict(int))
        pd.update(self.firebase.get(self.party_name, None) or {})
        return pd

    def run(self):
        self.keep_running = True
        while self.keep_running:
            try:
                self.keep_running = self.tick()
            except Exception:
                logging.exception("AH DAEMON PROBLEM")
            time.sleep(1)

    def _vote_score(self, track):
      votes = track['votes'].values()
      upvotes = filter(lambda x: x == "like", votes)
      downvotes = filter(lambda x: x == "dislike", votes)
      return len(upvotes) - len(downvotes)

    def _track_comparator(self, track_a, track_b):
        a_score = self._vote_score(track_a)
        b_score = self._vote_score(track_b)
        if a_score == b_score:
          try:
            a_time = parser.parse(track_a['timestamp'])
            b_time = parser.parse(track_b['timestamp'])
            return -cmp(a_time, b_time)
          except KeyError:
            pass
        return cmp(a_score, b_score)

    def play_next_track(self):
        if 'queue' in self.party_data:
            queue = self.party_data['queue']
            ordered_tracks = sorted(queue.values(), cmp=self._track_comparator, reverse=True)
            try:
                next_track = ordered_tracks[0]
            except IndexError:
                next_track = None
            if next_track:
                self.firebase.delete(self.party_name + '/queue', next_track['id'])
                self.play_track(next_track)
            else:
                self.play_track(None)
        else:
            self.play_track(None)

    def send_play_track_message(self, rdio_track):
        message = {
            'artist': rdio_track['artist'],
            'title': rdio_track['name'],
            'iconUrl': rdio_track['icon'],
            'timestamp': datetime.utcnow().isoformat(),
            'trackUrl': rdio_track['shortUrl'],
            'trackKey': rdio_track['key'],
            'type': 'NewTrack'
        }
        self.firebase.post(self.party_name + "/messages/", message)

    def play_track(self, track):
        self.currently_playing = track
        player_object = {
            'position': 0,
            'playState': 1 if track else 0,
            'playingTrack': track
        }
        self.firebase.put(self.party_name, 'player', player_object)
        if track:
            track_key = track['trackKey']
            rdio_track = self.rdio.get(keys=track_key)[track_key]
            self.current_track_duration = rdio_track['duration']
            self.current_start_time = datetime.now()
            self.send_play_track_message(rdio_track)
        else:
            self.current_track_duration = None
            self.current_start_time = None
        self.reset_skippers()

    def get_skippers(self):
        try:
            return dict([
                (skipper['key'], skipper) for skipper in self.party_data['skippers'].values()
            ]).values()
        except KeyError:
            return []

    def get_online_users(self):
        return [
            user for user in self.party_data.get('people', {}).values() if user['isOnline']
        ]

    def should_skip(self):
        return len(self.get_skippers()) > len(self.get_online_users()) / 2

    def tick(self):
        self.party_data = self.get_party_data()
        position = (datetime.now() - (self.current_start_time or datetime.now())).seconds
        if (not self.currently_playing or position > self.current_track_duration or self.should_skip()):
            self.play_next_track()
        else:
            self.firebase.put(self.party_name + '/player/', 'position', position)
        return self.should_keep_running()

    def reset_skippers(self):
        self.firebase.delete(self.party_name, 'skippers')

    def should_keep_running(self):
        """ Kill if no one is online in the room any more """
        people = self.party_data['people']
        users_online = bool([
            person for person in people.values() if person['isOnline']
        ])
        if users_online:
            self.last_saw_users = datetime.now()

        if not users_online and (datetime.now() - self.last_saw_users) > WAIT_FOR_USERS:
            return False
        else:
            return True
