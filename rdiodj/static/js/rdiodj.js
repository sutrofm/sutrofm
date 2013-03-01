/*globals app, console, R, Backbone, Firebase, rdioUserKey, firebaseToken */

window.app = window.app || {};

app.currentUserKey = rdioUserKey;

app.Track = Backbone.Model.extend({
  LIKE: 'like',
  DISLIKE: 'dislike',

  defaults: {
    "trackKey": null,
    "userKey": null,
    "votes": {},
    "upVotes": 0,
    "downVotes": 0
  },

  getVoteRef: function() {
    return this.collection.firebase.child(this.get('id')).child('votes');
  },

  vote: function(newVote) {
    console.info('Voting', newVote, 'for', this.get('trackKey'));
    this.getVoteRef().child(app.currentUserKey).set(newVote);
    this.updateVoteCounts();
  },

  upVote: function() {
    this.vote(this.LIKE);
  },

  downVote: function() {
    this.vote(this.DISLIKE);
  },

  getVoteCount: function(votes, voteType) {
    var self = this;
    var count = _.reduce(votes, function(num, vote) {
      if (vote === voteType) {
        return num + 1;
      } else {
        return num;
      }
    }, 0);
    return count;
  },

  updateVoteCounts: function() {
    var votes = _.values(this.get('votes'));
    var likeCount = this.getVoteCount(votes, this.LIKE);
    var dislikeCount = this.getVoteCount(votes, this.DISLIKE);

    console.log('Updated vote count', 'like', likeCount, 'dislike', dislikeCount);

    this.set({
      upVotes: likeCount,
      downVotes: dislikeCount
    });
  }

});


app.TrackList = Backbone.Firebase.Collection.extend({
  model: app.Track,

  firebase: 'https://rdiodj.firebaseio.com/room/queue',

  comparator: function(track) {
    return (track.get('upVotes') - track.get('downVotes')) * -1;
  }

});

app.queue = new app.TrackList();

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

    R.player.on("change:playingTrack", function(newValue) {
      if (newValue !== null) {
        self.rdioTrack = newValue;
        self.render();
      }
    });

    R.player.on("change:playState", function(newValue) {
      if (newValue === R.player.PLAYSTATE_STOPPED) {
        self.playNext();
      }
    });

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
    if (!app.queue.length) {
      return;
    }

    var queueItem = app.queue.shift();
    console.log('Playing next track', queueItem);

    this.addToHistory(queueItem);

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
      }, this.model.toJSON());
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
