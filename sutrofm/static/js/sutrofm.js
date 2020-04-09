/*globals app, console, R, Backbone, rdioUserKey*/

window.app = window.app || {};

// app.currentUserKey = rdioUserKey;

app.Player = Backbone.Model.extend({
  setState: function(data) {
    this.set('position', data['playing_track_position']);
    this.set('playingTrack', {
      'trackKey': data['playing_track_key'],
      'userKey': data['playing_track_user_key']
    });
  }
});

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
    // This method is broken because we don't have timestamp set in attributes of chat.messageHistory entries since the redis rewrite
    // But the good news is it isn't linked to from anywhere at the moment, yay!
    var playlistName = 'sutro.fm "' + this.getRoomString() + '" ' + this.getDateString();
    this.trackIds = chat.messageHistory.map(
      function(x) {
        var twelve_hours_in_ms = 43200000;
        var today = new Date();
        var timestamp = new Date(x.attributes.timestamp);
        if (x.attributes.messageType == 'new_track' && Math.abs(today - timestamp) < twelve_hours_in_ms) {
          return x.attributes.trackKey;
        }
      }
    );
    R.request({
      method: 'createPlaylist',
      content: {
        name: playlistName,
        description: 'Lovingly created with http://sutro.fm!',
        tracks: this.trackIds
      },
      success: function(response) {
        console.log('playlist created');
      },
      error: function(response) {
        console.log('playlist probably not created');
      }
    });
    this.snapped = true;
    this.playlist = playlistName;
    this.render();
    self = this;
    setTimeout(function () {self.snapped = false; self.render();}, 5000);
  },

  onPlaylistRoomHistoryClick: function() {
    var playlistName = 'sutro.fm "' + this.getRoomString() + '" ' + this.getDateString();
    this.trackIds = chat.messageHistory.map(function(x) { if (x.attributes.messageType == 'new_track') { return x.attributes.trackKey; } });
    R.request({
      method: 'createPlaylist',
      content: {
        name: playlistName,
        description: 'Lovingly created with http://sutro.fm!',
        tracks: this.trackIds
      },
      success: function(response) {
        console.log('playlist created');
      },
      error: function(response) {
        console.log('playlist probably not created');
      }
    });
    this.snapped = true;
    this.playlist = playlistName;
    this.render();
    self = this;
    setTimeout(function () {self.snapped = false; self.render();}, 5000);
  }
});

formatDuration = function(duration) {
  var durationInSecs = duration;
  var durationMins = Math.floor(duration / 60);
  var durationSecs = String(duration % 60);
  if (durationSecs.length < 2)
    durationSecs = "0" + durationSecs;
  return durationMins + ":" + durationSecs;
},


app.Track = Backbone.Model.extend({
  upVote: function() {
    $.ajax({
      'url': '/api/v2/votes/',
      'method': 'POST',
      'data': {
        // TODO: get these values
        "user": null,
        "queue_item": this.get('queueEntryId'),
        "value": 1,
        "is_skip": false
      }
    });
  },

  downVote: function() {
    $.ajax({
      'url': '/api/v2/votes/',
      'method': 'POST',
        'data': {
            // TODO: get these values
            "user": null,
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
        'userKey': value['user_key']
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
            'method': 'POST',
            'data': {
                // TODO: get these values
                "user": null,
                "queue_item": this.get('queueEntryId'),
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
      this.isFavorited = false;
      $('#favorite-button').removeClass("was_favorited").addClass("not_favorited");
      R.request({
        method: 'removeFromFavorites',
        content: {
          keys: [app.nowPlayingView.rdioTrackKey]
        },
        success: function(response) {
          chat.sendMessage("unfavorited this track");
        }
      });
    },

    favoriteCurrentlyPlaying: function() {
      this.isFavorited = true;
      $('#favorite-button').removeClass("not_favorited").addClass("was_favorited");
      R.request({
        method: 'addToFavorites',
        content: {
          keys: [app.nowPlayingView.rdioTrackKey]
        },
        success: function(response) {
          chat.sendMessage("favorited this track");
        }
      });
    },
});

app.NowPlayingView = Backbone.View.extend({
  model: app.Track,

  el: '#now-playing',

  template: _.template($('#now-playing-template').html()),

  events: {
    'click #favorite-button': '_clickFavorites',
    'click .mute': '_handleMuteClick',
    'click .music': '_handleSpeakerClick'
  },

  initialize: function() {
    var self = this;
    this.rdioTrackKey = null;
    this.activeUsers = chat.activeUsers;
    this.playState = app.playState;

    _.bindAll(this, '_onPositionChange');
    this.render()
  },

  _onPositionChange: function(position) {
    prettyPosition = formatDuration(position);
    if (R.player.playingTrack()) {
      prettyDuration = formatDuration(R.player.playingTrack().get('duration'));
      this.$(".timer").text(prettyPosition + "/" + prettyDuration);
      this.$(".duration-bar > span").animate({ width: ( position / R.player.playingTrack().get('duration') ) * 100+'%' }, 100);
    }
  },

  getDuration: function(duration) {
    return formatDuration(duration);
  },

  _handleMuteClick: function() {
    if (R.player.volume() > 0.5) {
      R.player.volume(0);
    } else {
      R.player.volume(1);
    }
  },

  _handleSpeakerClick: function() {
    R.player.startMasterTakeover();
    R.player.volume(1);
    if (app.playState.get('playingTrack') && app.playState.get('position')) {
      console.log("Jumping player to track '"+app.playState.get('playingTrack')+"' @ "+app.playState.get('position')+"s");
      R.player.play({
        source: app.playState.get('playingTrack').trackKey,
        initialPosition: app.playState.get('position')
      });
    }
  },

  initChildModels: function(favoritedTrack) {
    this.skipButton = new app.SkipButton();
    this.favoriteButton = new app.FavoriteButton(favoritedTrack);
  },

  _clickFavorites: function() {
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

  render: function() {
    var self = this;
    var keys = [this.rdioTrackKey];
    var userKey = null;
    if (self.playState.get('playingTrack')) {
      keys.push(self.playState.get('playingTrack').userKey);
      userKey = self.playState.get('playingTrack').userKey;
    }
    if (this.rdioTrackKey) {
      app.S.getTrack(this.rdioTrackKey, {}, (error, track) => {
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
        self.$el.html(self.template(data))
        self.$el.show()
        self.initChildModels(false);
        //$('#wrap').css('background-image', 'url('+response.result[self.rdioTrackKey].playerBackgroundUrl+')');
      })
      /*R.request({
        method: 'get',
        content: {
          keys: keys.join(","),
          extras: 'streamRegions,shortUrl,bigIcon,duration,dominantColor,playerBackgroundUrl,isInCollection'
        },
        success: function(response) {
          var userObj = (response.result[userKey]) ? response.result[userKey] : {firstName: '', lastName: ''};
          var addedByName = userObj.firstName + " " + userObj.lastName;
          var activeUsers = self.activeUsers;
          var masterUserObj = self.activeUsers.where({id:self.playState.get('masterUserKey')});
          var userName = null;
          var favorited = false;
          if (self.rdioTrackKey && response.result[self.rdioTrackKey]) {
            favorited = response.result[self.rdioTrackKey].isInCollection;
          }
          if (masterUserObj.length > 0 && masterUserObj[0]) {
            userName = masterUserObj[0].get('display_name');
          }
          if (self.rdioTrackKey) {
            var data = _.extend({
              'track': response.result[self.rdioTrackKey],
              'formattedDuration': self.getDuration(response.result[self.rdioTrackKey].duration),
              'masterUser': userName,
              'addedBy': addedByName,
              'favorited': favorited
            });
            self.$el.html(self.template(data));
            self.$el.show();
            self.initChildModels(favorited);
            $('#wrap').css('background-image', 'url('+response.result[self.rdioTrackKey].playerBackgroundUrl+')');
          } else {
            self.$el.hide();
          }
        },
        error: function(response) {
          console.log('Unable to get track information for', self.rdioTrackKey);
        }
      });*/

    } else {
      this.$el.hide();
    }
    return this;
  },

  /**
   * Called when the client should listen to a remote player
   **/
  initSlaveStatus: function() {
    console.info('Becoming slave');

    app.playState.on('change:playingTrack', this._onSlaveTrackChange, this);
    app.playState.on('change:playState', this._onSlavePlayerStateChange, this);
  },

  _onSlaveTrackChange: function(model, value, options) {
    if (value.trackKey) {
        this.rdioTrackKey = value.trackKey
        this.render()
    } else {
      this.render();
    }
  },

  _onSlavePlayerStateChange: function(model, value, options) {
    switch (value) {
      case R.player.PLAYSTATE_PAUSED:
      case R.player.PLAYSTATE_STOPPED:
        R.player.pause();
        break;
      case R.player.PLAYSTATE_PLAYING:
        R.player.play();
        break;
    }
  }
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
    this.rdioTrack = null;
    this.rdioUser = null;

    var self = this;
    if (!self.rdioTrack) {
        app.S.getTrack(self.model.get('trackKey'), {}, (error, track) => {
            self.rdioTrack = {
                icon: track.album.images[0].url,
                shortUrl: 'http://twitter.com/marekkapolka',
                name: track.name,
                artist: track.artists.map((a)=> a.name).join(", ")
            }
            self.rdioUser = {
                shortUrl: 'http://twitter.com/mkapolka',
                key: self.model.get('userKey'),
                name: self.model.get("userKey")
            }
            self.trackDuration = track.duration_ms
            self.render()
        })
    }
  },

  render: function() {
    if (this.rdioTrack && this.rdioUser) {
      var data = _.extend({
        'track': this.rdioTrack,
        'user': this.rdioUser,
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
    console.log('Removing track ' + this.rdioTrack.name);
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

app.ThemeInfo = Backbone.Model.extend({
  setTheme: function(data) {
    this.set({'themeText': data['theme']})
  },
}),

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

app.receiveMessage = function(msg) {
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


$(function() {
  self.redis = WS4Redis({
    uri: window.websocket_uri + "parties:" + window.roomId + "?subscribe-broadcast&publish-broadcast&echo",
    receive_message: app.receiveMessage,
    heartbeat_msg: window.heartbeat_msg
  });

  $.ajaxSetup({
      beforeSend: function(xhr, settings) {
          if (settings.method === "POST") {
              xhr.setRequestHeader("X-CSRFToken", $("[name=csrfmiddlewaretoken]").val())
          }
      }
  });


  app.S = new app.SpotifyAPI()
  app.S.setAccessToken(window.spotify_access_token)

  app.playState = new app.Player();
  var queueView = new app.queueView();
  app.nowPlayingView = new app.NowPlayingView();
  var searchView = new app.SearchView();
  var playlistView = new app.PlaylistView();
  app.themeModel = new app.ThemeInfo();
  app.themeView = new app.ThemeView({model: app.themeModel});
  app.nowPlayingView.initSlaveStatus();
  var skipButton = new app.SkipButton();

  app.playState.setState(window.initial_player_state);
  app.queue.setQueue(window.initial_queue_state);
  chat.activeUsers.setUserList(window.initial_user_list_state);
  chat.messageHistory.setMessages(window.initial_messages_state);
  app.themeModel.setTheme(window.initial_theme_state);

  setInterval(ping, 1000);

});
