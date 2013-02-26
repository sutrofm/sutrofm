var app = app || {};

app.Track = Backbone.Model.extend({
  getVoteRef: function() {
    return this.collection.firebase.child(this.get('id')).child('votes');
  },

  upVote: function() {
    var self = this;
    console.log('Up-voting', this.get('trackKey'));

    var voteRef = this.getVoteRef();
    voteRef.transaction(function(currentValue) {
      return currentValue + 1;
    }, function(error, committed, snapshot) {
      // TODO: Handle this error
      console.log('Was there an error? ' + error);
      console.log('Did we commit the transaction? ' + committed);
      console.log('The final value is: ' + snapshot.val());

      self.collection.sort();
    });
  },

  downVote: function() {
    var self = this;
    console.log('Down-voting', this.get('trackKey'));

    var voteRef = this.getVoteRef();
    voteRef.transaction(function(currentValue) {
      return currentValue - 1;
    }, function(error, committed, snapshot) {
      // TODO: Handle this error
      console.log('Was there an error? ' + error);
      console.log('Did we commit the transaction? ' + committed);
      console.log('The final value is: ' + snapshot.val());

      self.collection.sort();
    });
  }

});


app.TrackList = Backbone.Firebase.Collection.extend({
  model: app.Track,

  firebase: 'https://rdiodj.firebaseio.com/room/queue',

  comparator: function(track) {
    return track.get('votes') * -1;
  }

});

app.queue = new app.TrackList();

app.NowPlayingView = Backbone.View.extend({
  el: '#now-playing',

  template: _.template($('#now-playing-template').html()),

  events: {
    'click #player-play': 'beginPlaying'
  },

  initialize: function() {
    var self = this;
    this.rdioTrack = null;
    this.rdioUser = null;

    R.player.on("change:playingTrack", function(newValue) {
      console.log("Now playing track ", newValue);
      self.rdioTrack = newValue.attributes;
      self.render();
    });

  },

  render: function() {
    if (this.rdioTrack) {
      var data = _.extend({
        'track': this.rdioTrack
      });
      this.$el.html(this.template(data));
      this.$el.show();
    } else {
      this.$el.hide();
    }
    return this;
  },

  beginPlaying: function() {
    R.player.queue.play(0);
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
        'user': this.rdioUser,
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
    console.log('addOne', model, collection, options);
    var view = new app.TrackView({ model: model });
    this.$el.append(view.render().el);
  },

  addAll: function (collection, options) {
    console.log('addAll', collection, options);

    // Render the queue
    this.$el.empty();
    collection.each(this.addOne, this);

    // Update play queue
    R.player.queue.clear();
    _.each(collection.pluck('trackKey'), R.player.queue.add);
  }
});

R.ready(function() {
  var firebaseRef = new Firebase('https://rdiodj.firebaseio.com/');
  firebaseRef.auth(firebaseToken, function(error) {
    if (error) {
      console.log('Login Failed!', error);
    } else {
      console.log('Login Succeeded!');

      var queueView = new app.queueView();
      var nowPlayingView = new app.NowPlayingView();

      // Queue a new track
      $('#play-track-form').submit(function(event) {
        event.preventDefault();
        app.queue.add({
          trackKey: $('#track-key-input').val(),
          userKey: rdioUserKey,
          votes: 1
        });
        console.log(app.queue);
        return false;
      });
    }
  });
});
