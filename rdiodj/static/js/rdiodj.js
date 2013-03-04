/*globals app, console, R, Backbone, Firebase, rdioUserKey, firebaseToken */

window.app = window.app || {};

app.currentUserKey = rdioUserKey;

app.roomUrl = firebaseRootUrl;

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
  },

  getVoteCount: function(voteType) {
    var votes = _.values(this.get('votes'));
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
    var likeCount = this.getVoteCount(this.LIKE);
    var dislikeCount = this.getVoteCount(this.DISLIKE);

    console.log('Did vote count:', 'like', likeCount, 'dislike', dislikeCount);
    return {
      upVotes: likeCount,
      downVotes: dislikeCount
    };
  }

});


app.TrackList = Backbone.Firebase.Collection.extend({
  model: app.Track,

  firebase: app.roomUrl + '/queue',

  comparator: function(track) {
    var counts = track.getVoteCounts();
    return (counts.upVotes - counts.downVotes) * -1;
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
    this.rdioTrackKey = null;
    this.activeUsers = chat.activeUsers;
    this.playState = app.playState;

    this.listenTo(this.playState, 'change', function(model, newValue, options) {
      console.log('change:masterUserKey', model, newValue, options);
    });

    this.listenTo(this.playState, 'change:masterUserKey', function(model, newValue, options) {
      console.log('change:masterUserKey', model, newValue, options);
      if (newValue === undefined) {
        self.findNewMasterKey();
      }
    });

    R.player.on('change:playingTrack', function(newValue) {
      if (newValue !== null) {
        self.rdioTrackKey = newValue.get('key');
        self.render();
      }
    });

    if (this.playState.get('masterUserKey') === undefined) {
      this.findNewMasterKey();
    }

    if (this.playState.isMaster()) {
      this.initMasterStatus();
    } else {
      this.initSlaveStatus();
    }
  },

  render: function() {
    var self = this;

    if (this.rdioTrackKey) {
      R.request({
        method: 'get',
        content: {
          keys: this.rdioTrackKey,
          extras: 'streamRegions,shortUrl,bigIcon'
        },
        success: function(response) {
          var data = _.extend({
            'track': response.result[self.rdioTrackKey]
          });

          self.$el.html(self.template(data));
          self.$el.show();
        },
        error: function(response) {
          console.log('Unable to get tack information for', self.rdioTrackKey);
        }
      });

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

    this.playState.set({
      'playingTrack': queueItem.toJSON()
    });

    R.player.play({
      source: queueItem.get('trackKey')
    });
  },

  addToHistory: function(queueItem) {
    console.log('Adding to history', queueItem);
  },

  findNewMasterKey: function() {
    var onlineUsers = this.activeUsers.where({isOnline:true});
    this.playState.set({
      'masterUserKey': onlineUsers[0].get('id')
    });
  },

  /**
   * Called when this client assumes control of the player
   **/
  initMasterStatus: function() {
    var self = this;

    if (app.playState.get('playState') == R.player.PLAYSTATE_PLAYING) {
      R.player.play({
        source: app.playState.get('playingTrack').trackKey,
        initialPosition: app.playState.get('position')
      });
    } else {
      this.playNext();
    }

    // Delete user key reference on reference, will trigger search for new master
    var masterUserKeyRef = this.playState.firebase.child('masterUserKey');
    masterUserKeyRef.onDisconnect().set(null);

    R.player.on('change:playingTrack', function(newValue) {
      if (newValue === null) {
        self.playNext();
      }
    });

    R.player.on('change:playState', function(newValue) {
      self.playState.set({
        'playState': newValue
      });
    });

    R.player.on('change:position', function(newValue) {
      self.playState.set({
        'position': newValue
      });
    });
  },

  /**
   * Called when the client should listen to a remote player
   **/
  initSlaveStatus: function() {

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
        extras: 'streamRegions,shortUrl,bigIcon'
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
      }, this.model.toJSON(), this.model.getVoteCounts());
      this.$el.html(this.template(data));
      this.$el.show();
    } else {
      this.$el.hide();
    }
    return this;
  },

  upVote: function() {
    this.model.upVote();
    app.queue.sort();
  },

  downVote: function() {
    this.model.downVote();
    app.queue.sort();
  }

});

app.queueView = Backbone.View.extend({
  el: '#queue',

  statsTemplate: _.template($('#stats-template').html()),

  initialize: function() {
    this.queueStats = $('#queue-stats');

    this.listenTo(app.queue, 'add', this.addOne);
    // this.listenTo(app.queue, 'sort', this.addAll);
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
