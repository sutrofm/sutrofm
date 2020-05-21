/*globals app, console, R, Backbone, spotifyUserKey*/

window.app = window.app || {};

/*
 * MODELS
 */
// Fields
// ready: is the player ready to receive songs?
// position: Position of the currently playing track
// deviceId: ID of the currently playing device
// playingTrack: struct of:
//      playing_track_key: spotify ID of playing track
//      playing_track_user_key: spotify user id of the user who added this track
//      playing_queue_entry_id: queue entry id of the currently playing track
app.Player = Backbone.Model.extend({
  setState: function(data) {
    this.set("ready", data['ready']);
    this.set('position', data['playing_track_position']);
    this.set('playingTrack', {
      'trackKey': data['playing_track_key'],
      'userKey': data['playing_track_user_key'],
      'queueEntryId': data['playing_queue_entry_id']
    });
  }
});

app.Track = Backbone.Model.extend({
  upVote: function() {
    $.ajax({
      'url': '/api/v2/votes/',
      'method': 'PUT',
      'data': {
        "queue_item": this.get('queueEntryId'),
        "value": 1,
        "is_skip": false
      }
    });
  },

  downVote: function() {
    $.ajax({
      'url': '/api/v2/votes/',
      'method': 'PUT',
        'data': {
            "queue_item": this.get('queueEntryId'),
            "value": -1,
            "is_skip": false
        }
    });
  },

  getVoteCounts: function() {
    var likeCount = this.get('upvotes').length;
    var dislikeCount = this.get('downvotes').length;

    return {
      upVotes: likeCount,
      downVotes: dislikeCount,
      totalVotes: likeCount - dislikeCount
    };
  },

  getDuration: function(duration) {
    return formatDuration(duration);
  }
});

app.ThemeInfo = Backbone.Model.extend({
  setTheme: function(data) {
    this.set({'themeText': data['theme']})
  },
}),

/*
 * VIEWS
 */

app.PlaylistView = Backbone.View.extend({
  el: '.playlist',
  template: _.template($('#playlist-template').html()),

  events: {
    "click .playlist-today": "onPlaylistTodayClick",
    "click .playlist-room-history": "onPlaylistRoomHistoryClick"
  },

  initialize: function() {
    this.snapped = false;
    this.render();
  },

  render: function() {
    values = {
      'snapped': this.snapped,
      'playlist': this.playlist
    };
    this.$el.html(this.template(values));
    return this;
  },

  getDateString: function() {
    var today = new Date();
    var dd = today.getDate();
    var mm = today.getMonth()+1;
    var yyyy = today.getFullYear();
    if(dd < 10) {
        dd = '0' + dd;
    }
    if(mm < 10) {
        mm = '0' + mm;
    }
    today = yyyy + '-' + mm + '-' + dd;
    return today;
  },

  getRoomString: function() {
    var roomUrlList = window.location.href.split('/');
    var roomString = roomUrlList[roomUrlList.length-2].replace(/_/g, ' ');
    return roomString;
  },

  onPlaylistTodayClick: function() {
    // TODO: Should create a playlist out of the songs played in the room today
  },

  onPlaylistRoomHistoryClick: function() {
    // TODO: Make a playlist out of all the songs that were played in this room.
  }
});

formatDuration = function(duration) {
  var durationInSecs = duration;
  var durationMins = Math.floor(duration / 60);
  var durationSecs = String(duration % 60);
  if (durationSecs.length < 2)
    durationSecs = "0" + durationSecs;
  return durationMins + ":" + durationSecs;
}


app.TrackList = Backbone.Collection.extend({
  model: app.Track,

  setQueue: function(data) {
    var queue = data.map(function(value) {
      var transformed_data = {
        'trackKey': value['track_key'],
        'queueEntryId': value['queue_entry_id'],
        'submitter': value['submitter'],
        'upvotes': value['upvotes'],
        'downvotes': value['downvotes'],
        'timestamp': value['timestamp'],
        'userKey': value['user_key'],
        'userUrl': value['user_url']
      };
      return new app.Track(transformed_data);
    });
    this.reset(queue);
    this.sort();
  },

  comparator: function(a, b) {
    var aScore = a.getVoteCounts().totalVotes;
    var bScore = b.getVoteCounts().totalVotes;
    if (aScore == bScore) {
      var aTime = new Date(a.get('timestamp'));
      var bTime = new Date(b.get('timestamp'));
      if (aTime > bTime) {
        return 1;
      } else if (aTime < bTime) {
        return -1;
      } else {
        return 0;
      }
    }
    return bScore - aScore;
  }

});

app.queue = new app.TrackList();

app.SkipButton = Backbone.View.extend({
    el: "#skip-button",

    events: {
        'click': '_clickSkip'
    },

    _clickSkip: function() {
      chat.sendMessage('voted to skip');
        $.ajax({
            'url': '/api/v2/votes/',
            'method': 'PUT',
            'data': {
                "queue_item": this.model.get('playingTrack').queueEntryId,
                "value": -1,
                "is_skip": true
            }
        });
    }
});

app.FavoriteButton = Backbone.View.extend({
    el: "#favorite-button",

    events: {
        'click': '_clickFavorite'
    },

    initialize: function(isFavorited) {
        this.isFavorited = isFavorited;
        if (this.isFavorited) {
          $('#favorite-button').removeClass("not_favorited").addClass("was_favorited");
        }
    },

    _clickFavorite: function() {
        if (this.isFavorited) {
            this.unfavoriteCurrentlyPlaying();
        } else {
            this.favoriteCurrentlyPlaying();
        }
    },

    unfavoriteCurrentlyPlaying: function() {
      app.S.removeFromMySavedTracks([app.nowPlayingView.spotifyTrackKey])
          .then(() => {
            this.isFavorited = false;
            $('#favorite-button').removeClass("was_favorited").addClass("not_favorited");
            chat.sendMessage("unfavorited this track");
          })
          .catch((err) => {console.log('Failed to unfavorite ' + app.nowPlayingView.spotifyTrackKey, err)})
    },

    favoriteCurrentlyPlaying: function() {
      app.S.addToMySavedTracks([app.nowPlayingView.spotifyTrackKey])
          .then(() => {
            this.isFavorited = true;
            $('#favorite-button').removeClass("not_favorited").addClass("was_favorited");
            chat.sendMessage("favorited this track");
          })
          .catch((err) => {console.log('Failed to favorite ' + app.nowPlayingView.spotifyTrackKey, err)})
    },
});

// Model = app.playState (Player)
app.NowPlayingView = Backbone.View.extend({
  el: '#now-playing',

  template: _.template($('#now-playing-template').html()),

  events: {
    'click #favorite-button': '_clickFavorites',
    'click .mute': '_handleMuteClick',
    'click .music': '_handleSpeakerClick'
  },

  initialize: function() {
    var self = this;
    this.spotifyTrackKey = null;
    this.activeUsers = chat.activeUsers;
    this.playState = app.playState;

    // _.bindAll(this, '_onPositionChange');
    setInterval(this.updatePlayerState, 1000);
    this.render()
  },

   updatePlayerState: function() {
    var player = app.playState.get('spotifyPlayer');
    if (player) {
      player.getCurrentState().then(state => {
        if (!state) {
            return;
        }
        prettyPosition = formatDuration(Math.floor(state.position / 1000));
        prettyDuration = formatDuration(Math.floor(state.duration / 1000));
        this.$(".timer").text(prettyPosition + "/" + prettyDuration);
        this.$(".duration-bar > span").animate({ width: ( state.position / state.duration ) * 100+'%' }, 100);
      });
    }
  },

  getDuration: function(duration) {
    return formatDuration(duration);
  },

  _handleMuteClick: function() {
      console.log('Toggling mute');
      var player = app.playState.get('spotifyPlayer');
      player.getVolume().then(volume => {
        if (volume > 0.5) {
            player.setVolume(0);
        } else {
            player.setVolume(1);
        }
      })
  },

  _handleSpeakerClick: function() {
    // TODO: Should begin playing spotify via the embedded player
    if (app.playState.get('playingTrack') && app.playState.get('position')) {
      console.log("Jumping player to track '"+app.playState.get('playingTrack')+"' @ "+app.playState.get('position')+"s");
    }
  },

  initChildModels: function() {
    this.skipButton = new app.SkipButton({
        model: this.model
    });

    app.S.containsMySavedTracks([this.spotifyTrackKey])
        .then((favResults) => {
          console.log('Track is favorite: ', favResults[0]);
          this.favoriteButton = new app.FavoriteButton(favResults[0]);
        })
        .catch((err) => {
          console.log('Error checking if track is favorite: ', err);
          this.favoriteButton = new app.FavoriteButton(false);
        })

  },

  _clickFavorites: function() {
  },

  render: function() {
    var self = this;
    if (app.playState.get('spotifyPlayer') && this.spotifyTrackKey) {
      // Set up the background color
        console.log("Track Key: ", this.spotifyTrackKey)
      getTrack(this.spotifyTrackKey, (error, track) => {
        window.Vibrant.from(track.album.images[0].url).getPalette(function(err, palette) {
            if (palette) {
                $('#wrap').css('background', palette.DarkVibrant.getHex())
            }
        })
        var data = _.extend({
            track: {
                bigIcon: track.album.images[0].url,
                name: track.name,
                url: track.shortUrl,
                album: track.album.name,
                artist: track.artists.map(a => a.name).join(", ")
            },
            addedBy: self.playState.get('playingTrack').userKey
        })
        let payload = {
            uris: [track.uri],
            position_ms: this.playState.get("position") * 1000,
        }
        let deviceId = this.playState.get('deviceId')
        if (deviceId) {
            payload.device_id = deviceId
        }
        app.S.play(payload)
        self.$el.html(self.template(data))
        self.$el.show()
        self.initChildModels();
      })
    } else {
      if (app.playState.get('spotifyPlayer') !== undefined) {
        app.S.pause(console.log)
      }
      this.$el.hide();
    }
    return this;
  },

  play: function() {
      if (this.spotifyTrackKey) {
          getTrack(this.spotifyTrackKey, (error, track) => {
            let payload = {
                uris: [track.uri],
                position_ms: this.playState.get("position") * 1000,
            }
            let deviceId = this.playState.get("deviceId")
            if (deviceId) {
                payload.device_id = deviceId;
            }
            app.S.play(payload)
          })
      }
  },

  /**
   * Called when the client should listen to a remote player
   **/
  init: function() {
    console.info('Becoming slave');

    app.playState.on('change:playingTrack', this._onPlayerTrackChange, this);
    app.playState.on('change:playState', this._onPlayerStateChange, this);
    app.playState.on('change:deviceId', this.render, this);
    app.playState.on('change:ready', this._onReadinessUpdated, this);
  },

  _onReadinessUpdated: function(model, value, options) {
    if (value === true) {
        this.render()
    }
  },

  _onPlayerTrackChange: function(model, value, options) {
    if (value.trackKey) {
        this.spotifyTrackKey = value.trackKey
        this.render()
    } else {
      this.spotifyTrackKey = null
      this.render();
    }
  },
});

app.TrackView = Backbone.View.extend({
  tagName: 'li',

  template: _.template($('#track-template').html()),
  events: {
    'click .up-vote': 'upVote',
    'click .down-vote': 'downVote',
    'click .remove-track': 'removeTrack'
  },

  initialize: function() {
    this.listenTo(this.model, 'change', this.render);
    this.listenTo(this.model, 'remove', this.remove);
    this.spotifyTrack = null;
    this.spotifyUser = null;

    var self = this;
    if (!self.spotifyTrack) {
        getTrack(self.model.get('trackKey'), (error, track) => {
            self.spotifyTrack = {
                icon: track.album.images[0].url,
                shortUrl: track.external_urls.spotify,
                name: track.name,
                artist: track.artists.map((a)=> a.name).join(", "),
            }
            self.spotifyUser = {
                shortUrl: self.model.get('userUrl'),
                key: self.model.get('userKey'),
                name: self.model.get("userKey")
            }
            self.trackDuration = formatDuration(Math.floor(track.duration_ms / 1000))
            self.render()
        })
    }
  },

  render: function() {
    if (this.spotifyTrack && this.spotifyUser) {
      var data = _.extend({
        'track': this.spotifyTrack,
        'user': this.spotifyUser,
        'formattedDuration': this.trackDuration,
      }, this.model.toJSON(), this.model.getVoteCounts());
      this.$el.html(this.template(data));
      this.$el.show();
    } else {
      this.$el.hide();
    }
    return this;
  },

  getDuration: function(duration) {
    return formatDuration(duration);
  },

  upVote: function() {
    this.model.upVote();
    app.queue.sort();
  },

  downVote: function() {
    this.model.downVote();
    app.queue.sort();
  },

  removeTrack: function() {
    console.log('Removing track ' + this.spotifyTrack.name);
    $.ajax({
      'url': '/api/party/' + window.roomId + '/queue/remove',
      'method': 'POST',
      'data': {
        'id': this.model.get('queueEntryId')
      }
    });
  },

});

app.queueView = Backbone.View.extend({
  el: '#queue',

  statsTemplate: _.template($('#stats-template').html()),

  initialize: function() {
    this.queueStats = $('#queue-stats');

    this.listenTo(app.queue, 'add', this.addOne);
    this.listenTo(app.queue, 'reset', this.addAll);
    this.listenTo(app.queue, 'sort', this.addAll);
    this.listenTo(app.queue, 'change', this.sortQueue);
    this.listenTo(app.queue, 'all', this.render);
    //this.addAll(app.queue, {});
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

app.ThemeView = Backbone.View.extend({
  el: '#theme',

  template: _.template($('#theme-template').html()),

  events: {
    "click .theme_name": "onThemeClick",
    "keyup .theme_text": "onThemeTextSubmit"
  },

  initialize: function() {
    this.editing = false;

    this.listenTo(this.model, "change", this.render);
    this.render();
  },

  render: function() {
    var values = {
        'editing': this.editing,
    };
    this.$el.html(this.template(values));
    if (!this.editing) {
      this.$el.find('.theme_name').text(this.model.get('themeText'));
    }
    $(".theme_text").focus();
    return this;
  },

  onThemeTextSubmit: function(e) {
    if (e.keyCode == 13 && $(".theme_text").val()) {
      this.model.set('themeText', $(".theme_text").val());
      this.editing = false;
      this.render();
      $.ajax({
        'url': '/api/party/' + window.roomId + '/theme/set',
        'method': 'POST',
        'data': {
          'theme': this.model.get('themeText')
        }
    });
    }
  },

  onThemeClick: function() {
    this.editing = true;
    this.render();
  }
});

app.receiveMessage = function(event) {
  let msg = event.data
  console.log("Received message: ", msg)
  if (msg !== window.heartbeat_msg) {
    var payload = JSON.parse(msg);
    var type = payload['type'];
    switch (type) {
      case "player":
        app.playState.setState(payload['data']);
      break;

      case "queue":
        app.queue.setQueue(payload['data']);
      break;

      case "user_list":
        chat.activeUsers.setUserList(payload['data']);
      break;

      case "messages":
        chat.messageHistory.setMessages(payload['data']);
      break;

      case "message_added":
        chat.messageHistory.addMessage(payload['data']);
      break;

      case "theme":
        app.themeModel.setTheme(payload['data']);
      break;
    }
  }
};


function ping() {
  var roomId = window.roomId;
  $.ajax({
    'method': 'GET',
    'url': '/api/v2/parties/' + window.roomId + '/ping/'
  })
  .fail(function (response) {
    console.log('Could not ping the server to say that we are still in the party.');
  });
}

var spotifyCache = {}
function getTrack(id, callback) {
    if (id in spotifyCache) {
        return callback(null, spotifyCache[id])
    } else {
        app.S.getTrack(id, {}, (error, track) => {
            spotifyCache[id] = track
            callback(null, track)
        })
    }
}


$(function() {
  $.ajaxSetup({
      beforeSend: function(xhr, settings) {
          if (settings.method === "POST" ||
              settings.method === "PUT") {
              xhr.setRequestHeader("X-CSRFToken", $("[name=csrfmiddlewaretoken]").val())
          }
      }
  });

  var websocketProtocol = 'wss://';
  if (location.protocol !== "https:") {
    websocketProtocol = 'ws://'
  }

  window.websocket = new ReconnectingWebSocket(websocketProtocol + window.location.host + "/ws/party/" + window.roomId + "/");
  websocket.onmessage = app.receiveMessage

  app.S = new app.SpotifyAPI()
  app.S.setAccessToken(window.spotify_access_token)

  app.playState = new app.Player();
  var queueView = new app.queueView();
  app.nowPlayingView = new app.NowPlayingView({
    model: app.playState
  });
  var searchView = new app.SearchView();
  var playlistView = new app.PlaylistView();
  app.themeModel = new app.ThemeInfo();
  app.themeView = new app.ThemeView({model: app.themeModel});
  app.nowPlayingView.init();
  var skipButton = new app.SkipButton();

  app.playState.setState(window.initial_player_state);
  app.queue.setQueue(window.initial_queue_state);
  chat.activeUsers.setUserList(window.initial_user_list_state);
  chat.messageHistory.setMessages(window.initial_messages_state);
  app.themeModel.setTheme(window.initial_theme_state);

  setInterval(ping, 10000);
});
