/*globals app, console, R, Backbone, Firebase, rdioUserKey, firebaseToken */

window.app = window.app || {};

app.currentUserKey = rdioUserKey;

app.roomUrl = 'https://rdiodj.firebaseio.com/room';

app.Player = Backbone.Firebase.Model.extend({

  isMaster: function () {
    return this.get('masterUserKey') === app.currentUserKey;
  },

  firebase: app.roomUrl + '/player'

});

app.Track = Backbone.Model.extend({
  LIKE: 'like',
  DISLIKE: 'dislike',

  getVoteRef: function() {
    return this.collection.firebase.child(this.get('id')).child('votes');
  },

  vote: function(newVote) {
    console.info('Voting', newVote, 'for', this.get('trackKey'));
    this.getVoteRef().child(app.currentUserKey).set(newVote);
  },

  upVote: function() {
    this.vote(this.LIKE);
  },

  downVote: function() {
    this.vote(this.DISLIKE);
  }

});


app.TrackList = Backbone.Firebase.Collection.extend({
  model: app.Track,

  firebase: app.roomUrl + '/queue',

  comparator: function(track) {
    return (track.get('upVotes') - track.get('downVotes')) * -1;
  }

});

app.queue = new app.TrackList();
app.playState = new app.Player();

app.NowPlayingView = Backbone.View.extend({
  el: '#now-playing',

  template: _.template($('#now-playing-template').html()),

  events: {
    'click #player-play': 'playNext'
  },

  initialize: function() {
    var self = this;
    this.rdioTrack = null;
    this.rdioUser = null;

    if (app.playState.get('masterUserKey') === undefined) {
      app.playState.set({
        'masterUserKey': app.currentUserKey
      });
    }

    R.player.on('change:playingTrack', function(newValue) {
      if (newValue !== null) {
        self.rdioTrack = newValue;
        self.render();
      }
    });

    if (app.playState.isMaster()) {
      // Master listener should remove the next item from the queue
      self.playNext();

      R.player.on('change:playingTrack', function(newValue) {
        if (newValue === null) {
          self.playNext();
        }
      });

      R.player.on('change:playState', function(newValue) {
        app.playState.set({
          'playState': newValue
        });
      });

      R.player.on('change:position', function(newValue) {
        app.playState.set({
          'position': newValue
        });
      });
    } else {
      // Slave listener, should listen to app.playState changes
      if (app.playState.get('playState') == R.player.PLAYSTATE_PLAYING) {
        R.player.play({
          source: app.playState.get('playingTrack').trackKey,
          initialPosition: app.playState.get('position')
        });
      }

      app.playState.on('change:playingTrack', function(model, value, options) {
        console.log('change:playingTrack', model, value, options);
        R.player.play({
          source: value.trackKey
        });
      });
      app.playState.on('change:playState', function(model, value, options) {
        console.log('change:playState', model, value, options);
        switch (value) {
          case R.player.PLAYSTATE_PAUSED:
          case R.player.PLAYSTATE_STOPPED:
            R.player.pause();
            break;
        }
      });
    }

  },

  render: function() {
    if (this.rdioTrack) {
      var data = _.extend({
        'track': this.rdioTrack.attributes
      });
      this.$el.html(this.template(data));
      this.$el.show();
    } else {
      this.$el.hide();
    }
    return this;
  },

  playNext: function() {
    console.log('current play status:', R.player.playState());
    if (!app.queue.length) {
      return;
    }

    var queueItem = app.queue.shift();
    console.log('Playing next track', queueItem);
    this.addToHistory(queueItem);

    app.playState.set({
      'playingTrack': queueItem.toJSON()
    });

    R.player.play({
      source: queueItem.get('trackKey')
    });
  },

  addToHistory: function(queueItem) {
    console.log('Adding to history', queueItem);
  }

});

app.TrackView = Backbone.View.extend({
  tagName: 'li',

  template: _.template($('#track-template').html()),

  events: {
    'click .up-vote': 'upVote',
    'click .down-vote': 'downVote'
  },

  initialize: function() {
    this.listenTo(this.model, 'change', this.render);
    this.listenTo(this.model, 'remove', this.remove);
    this.rdioTrack = null;
    this.rdioUser = null;

    var self = this;
    R.request({
      method: 'get',
      content: {
        keys: self.model.get('trackKey') + ',' + self.model.get('userKey'),
        extras: 'streamRegions,shortUrl'
      },
      success: function(response) {
        self.rdioTrack = response.result[self.model.get('trackKey')];
        self.rdioUser = response.result[self.model.get('userKey')];
        self.render();
      },
      error: function(response) {
        console.log('Unable to get tack information for', self.model.get('trackKey'));
      }
    });

  },

  render: function() {
    if (this.rdioTrack && this.rdioUser) {
      var data = _.extend({
        'track': this.rdioTrack,
        'user': this.rdioUser
      }, this.model.toJSON(), this.getVoteCounts());
      this.$el.html(this.template(data));
      this.$el.show();
    } else {
      this.$el.hide();
    }
    return this;
  },

  upVote: function() {
    this.model.upVote();
  },

  downVote: function() {
    this.model.downVote();
  },

  getVoteCount: function(votes, voteType) {
    var count = _.reduce(votes, function(num, vote) {
      if (vote === voteType) {
        return num + 1;
      } else {
        return num;
      }
    }, 0);
    return count;
  },

  getVoteCounts: function() {
    var votes = _.values(this.model.get('votes'));
    var likeCount = this.getVoteCount(votes, this.model.LIKE);
    var dislikeCount = this.getVoteCount(votes, this.model.DISLIKE);

    console.log('Updated vote count', votes, 'like', likeCount, 'dislike', dislikeCount);
    return {
      upVotes: likeCount,
      downVotes: dislikeCount
    };
  }

});

app.queueView = Backbone.View.extend({
  el: '#queue',

  statsTemplate: _.template($('#stats-template').html()),

  initialize: function() {
    this.queueStats = $('#queue-stats');

    this.listenTo(app.queue, 'add', this.addOne);
    this.listenTo(app.queue, 'sort', this.addAll);
    this.listenTo(app.queue, 'all', this.render);
    this.addAll(app.queue, {});
  },

  render: function() {
    if (app.queue.length) {
      this.queueStats.html(this.statsTemplate({queueSize: app.queue.length}));
      this.queueStats.show();
    } else {
      this.queueStats.hide();
    }
  },

  addOne: function (model, collection, options) {
    var view = new app.TrackView({ model: model });
    this.$el.append(view.render().el);
  },

  addAll: function (collection, options) {
    this.$el.empty();
    collection.each(this.addOne, this);
  }
});

R.ready(function() {
  firebaseRef.auth(firebaseToken, function(error) {
    if (error) {
      console.log('Login Failed!', error);
    } else {
      console.log('Login Succeeded!');

      var queueView = new app.queueView();
      var nowPlayingView = new app.NowPlayingView();
      var searchView = new app.SearchView();
    }
  });
});
