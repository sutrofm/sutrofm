/*globals app, console, R, Backbone, Firebase, rdioUserKey, firebaseToken, firebaseRootUrl, firebaseRef */

window.app = window.app || {};

app.currentUserKey = rdioUserKey;

app.roomUrl = firebaseRootUrl;

app.Player = Backbone.Firebase.Model.extend({

  isMaster: function () {
    return (this.get('masterUserKey') === app.currentUserKey) && app.currentUserKey;
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
    var voteArray = this.get('votes');
    if (voteArray === undefined) {
      return 0;
    }
    var votes = _.values(voteArray);
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

    return {
      upVotes: likeCount,
      downVotes: dislikeCount,
      totalVotes: likeCount - dislikeCount
    };
  },


});


app.TrackList = Backbone.Firebase.Collection.extend({
  model: app.Track,

  firebase: app.roomUrl + '/queue',

  comparator: function(a, b) {
    var aScore = a.getVoteCounts().totalVotes;
    var bScore = b.getVoteCounts().totalVotes;
    return bScore - aScore;
  }

});

app.queue = new app.TrackList();

app.SkipList = Backbone.Firebase.Collection.extend({
  model: chat.User,
  firebase: app.roomUrl + '/skippers',

  voteToSkip: function() {
    if (!this.contains(chat.currentUser)) {
      this.add(chat.currentUser);
      chat.sendMessage("Voted to skip");
    }
  },

  //HACK TODO there has got to be a better way to do this
  clear: function() {
    while (this.length > 0) {
      this.pop();
    }
  }
});

app.skipList = new app.SkipList();

app.NowPlayingView = Backbone.View.extend({
  el: '#now-playing',

  template: _.template($('#now-playing-template').html()),

  events: {
    'click #skip-button': '_clickSkip',
    'click #favorite-button': '_clickFavorites'
  },

  initialize: function() {
    var self = this;
    this.rdioTrackKey = null;
    this.activeUsers = chat.activeUsers;
    this.playState = app.playState;

    this.listenTo(this.playState, 'change:masterUserKey', this._onMasterUserKeyChange);
    this.listenTo(app.skipList, 'add', this._onSkipListUpdate);

    R.player.on('change:playingTrack', this._onPlayingTrackChange, this);

    if (this.playState.get('masterUserKey') === undefined) {
      this.findNewMasterKey();
    }

    if (this.playState.isMaster()) {
      this.initMasterStatus();
    } else {
      this.initSlaveStatus();
    }
  },

  _clickSkip: function() {
    app.skipList.voteToSkip();
  },

  _clickFavorites: function() {
    this.favoriteCurrentlyPlaying();
  },

  /**
   * Handles changes to masterUserKey
   */
  _onMasterUserKeyChange: function(model, newValue, options) {
    console.info('change:masterUserKey', newValue);
    if (newValue === undefined) {
      this.findNewMasterKey();
    } else if(newValue === app.currentUserKey) {
      this.initMasterStatus();
    } else {
      this.initSlaveStatus();
    }
  },

  /**
   * Handles changes to the currently playing track
   */
  _onPlayingTrackChange: function(newValue) {
    if (newValue === null) {
      this.rdioTrackKey = null;
    } else {
      this.rdioTrackKey = newValue.get('key');
    }

    this.render();
  },

  _onSkipListUpdate: function() {
    if (app.skipList.length > chat.activeUsers.getOnlineUsers().length / 2) {
      this.skipSong();
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
          var activeUsers = self.activeUsers;
          var masterUserObj = self.activeUsers.where({id:self.playState.get('masterUserKey')});
          var userName = null;
          if (masterUserObj.length > 0 && masterUserObj[0]) {
            userName = masterUserObj[0].get('fullName');
          }
          var data = _.extend({
            'track': response.result[self.rdioTrackKey],
            'masterUser': userName
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

  skipSong: function() {
    this.playNext();
  },

  playNext: function() {
    if (!app.queue.length) {
      this.playState.set({
        'playState': R.player.PLAYSTATE_STOPPED,
        'playingTrack': null
      });
      return;
    }

    var queueItem = app.queue.shift();
    console.log('Playing next track', queueItem);
    this.addToHistory(queueItem);
    app.skipList.clear();

    this.playState.set({
      'playingTrack': queueItem.toJSON()
    });

    R.player.play({
      source: queueItem.get('trackKey')
    });
  },

  addToHistory: function(queueItem) {
    // R.request here instead of in render, cause it's historical.
    var trackKey = queueItem.get('trackKey');
    R.request({
      method: 'get',
      content: {
        keys: trackKey,
        extras: '-*,name,artist,icon,shortUrl'
      },
      success: function(res) {
        var track = res.result[trackKey];
        var messageData = {
          type: 'NewTrack',
          title: track.name,
          artist: track.artist,
          iconUrl: track.icon,
          trackUrl: track.shortUrl,
          timestamp: (new Date()).toISOString()
        };

        chat.messageHistory.add(messageData);
      }
    });
  },

  favoriteCurrentlyPlaying: function() {
    R.request({
      method: 'addToFavorites',
      content: {
        keys: this.rdioTrackKey
      },
      success: function(response) {
        chat.sendMessage("favorited this track");
      }
    })
  },

  findNewMasterKey: function() {
    var self = this;
    this.playState.firebase.child('masterUserKey').transaction(function(currentValue) {
      console.log('Finding a new masterUserKey:', currentValue);
      var newUserKey = app.currentUserKey;

      if (self.activeUsers) {
        var onlineUsers = self.activeUsers.where({isOnline:true});
        var sortedOnlineUsers = _.sortBy(onlineUsers,
          function(user) { return user.get('id'); });

        newUserKey = sortedOnlineUsers[0].get('id');
      }

      if (currentValue === null) {
        return newUserKey;
      } else {
        return undefined;
      }
    }, function(error, committed, snapshot) {
      if (error) {
        console.warn('Error when setting masterUserKey:', error.message);
        if (committed) {
          console.warn('Transaction was committed:', snapshot);
        } else {
          console.warn('Transaction was not committed:', snapshot);
        }
      }
    });
  },

  /**
   * Called when this client assumes control of the player
   **/
  initMasterStatus: function() {
    var self = this;
    console.info('Becoming master');
    self.destroySlaveStatus();

    if (app.playState.get('playState') == R.player.PLAYSTATE_PLAYING) {
      R.player.play({
        source: app.playState.get('playingTrack').trackKey,
        initialPosition: app.playState.get('position')
      });
    } else {
      this.playNext();
    }

    // Delete user key reference on disconnect, which will trigger search for new master
    var masterUserKeyRef = this.playState.firebase.child('masterUserKey');
    masterUserKeyRef.onDisconnect().set(null);

    // When the current track finishes, play the next
    R.player.on('change:playingTrack', this._onMasterTrackChange, this);

    // Let the slaves know the master's player status
    R.player.on('change:playState', this._onMasterPlayerStateChange, this);

    // Let the slaves know the master's player position
    R.player.on('change:position', this._onMasterPlayerPositionChange, this);

    // When something is added to the queue and we aren't playing, play it
    this.listenTo(app.queue, 'add', this._onMasterQueueChange);
  },

  destroyMasterStatus: function() {
    var masterUserKeyRef = this.playState.firebase.child('masterUserKey');
    masterUserKeyRef.onDisconnect().cancel();

    R.player.off('change:playingTrack', this._onMasterTrackChange, this);
    R.player.off('change:playState', this._onMasterPlayerStateChange, this);
    R.player.off('change:position', this._onMasterPlayerPositionChange, this);
    this.stopListening(app.queue, 'add', this._onMasterQueueChange);
  },

  _onMasterTrackChange: function(newValue) {
    if (newValue === null) {
      this.playNext();
    }
  },

  _onMasterPlayerStateChange: function(newValue) {
    this.playState.set({
      'playState': newValue
    });
  },

  _onMasterPlayerPositionChange: function(newValue) {
    this.playState.set({
      'position': newValue
    });
  },

  _onMasterQueueChange: function(model, collection, options) {
    if (app.playState.get('playingTrack') === null) {
      this.playNext();
    }
  },

  /**
   * Called when the client should listen to a remote player
   **/
  initSlaveStatus: function() {
    console.info('Becoming slave');
    this.destroyMasterStatus();

    if (app.playState.get('playState') == R.player.PLAYSTATE_PLAYING) {
      R.player.play({
        source: app.playState.get('playingTrack').trackKey,
        initialPosition: app.playState.get('position')
      });
    }

    app.playState.on('change:playingTrack', this._onSlaveTrackChange, this);
    app.playState.on('change:playState', this._onSlavePlayerStateChange, this);
  },

  destroySlaveStatus: function() {
    app.playState.off('change:playingTrack', this._onSlaveTrackChange, this);
    app.playState.off('change:playState', this._onSlavePlayerStateChange, this);
  },

  _onSlaveTrackChange: function(model, value, options) {
    console.log('change:playingTrack', model, value, options);
    R.player.play({
      source: value.trackKey
    });
  },

  _onSlavePlayerStateChange: function(model, value, options) {
    console.log('change:playState', model, value, options);
    switch (value) {
      case R.player.PLAYSTATE_PAUSED:
      case R.player.PLAYSTATE_STOPPED:
        R.player.pause();
        break;
    }
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
    this.listenTo(app.queue, 'sort', this.addAll);
    this.listenTo(app.queue, 'change', this.sortQueue);
    this.listenTo(app.queue, 'all', this.render);
    this.addAll(app.queue, {});
  },

  render: function() {
    if (app.queue.length) {
      // this.queueStats.html(this.statsTemplate({queueSize: app.queue.length}));
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
  },

  sortQueue: function() {
    app.queue.sort();
  }
});

app.ThemeInfo = Backbone.Firebase.Model.extend({
  firebase: app.roomUrl + '/meta',
  getText: function() { return this.get('themeText') },
  setText: function(text) { this.set({'themeText': text}) },

}),

app.ThemeView = Backbone.View.extend({
  el: '#theme',

  template: _.template($('#theme-template').html()),

  events: {
    "click .theme_name": "onThemeClick",
    "keyup .theme_text": "onThemeTextSubmit"
  },

  initialize: function() {
    this.editing = false
    this.model.setText('no theme... just play whatever you want')
    this.listenTo(this.model, "change", this.render)
    this.render()
  },

  render: function() {
    var values = {
        'editing': this.editing,
        'themeText': this.model.getText()
    }
    this.$el.html(this.template(values));
    $(".theme_text").focus()
    return this;
  },

  onThemeTextSubmit: function(e) {
    if (e.keyCode == 13 && $(".theme_text").val()) {
      this.model.setText($(".theme_text").val())
      this.editing = false
      this.render()
    }
  },
  onThemeClick: function() {
    this.editing = true;
    this.render();
  }
})

R.ready(function() {
  firebaseRef.auth(firebaseToken, function(error) {
    if (error) {
      console.log('Login Failed!', error);
    } else {
      console.log('Login Succeeded!');

      app.playState = new app.Player();
      var queueView = new app.queueView();
      app.nowPlayingView = new app.NowPlayingView();
      var searchView = new app.SearchView();
      var themeView = new app.ThemeView({model: new app.ThemeInfo()});
    }
  });
});
