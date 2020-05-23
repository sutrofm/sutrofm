/*globals app, console, R, Backbone, spotifyUserKey*/

(function SutroFM() {
    window.app = window.app || {};

    formatDuration = function(duration) {
      var durationInSecs = duration;
      var durationMins = Math.floor(duration / 60);
      var durationSecs = String(duration % 60);
      if (durationSecs.length < 2)
        durationSecs = "0" + durationSecs;
      return durationMins + ":" + durationSecs;
    }

    /*
     * MODELS
     */
    // Fields
    // position: Position of the currently playing track
    // localDeviceId: ID of the local player device
    // playingTrack: struct of:
    //      playing_track_key: spotify ID of playing track
    //      playing_track_user_key: spotify user id of the user who added this track
    //      playing_queue_entry_id: queue entry id of the currently playing track
    app.Player = Backbone.Model.extend({
      setState: function(data) {
        this.set({
            position: data['playing_track_position'],
            trackKey: data['playing_track_key'],
            userKey: data['playing_track_user_key'],
            queueEntryId: data['playing_queue_entry_id']
        })
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
      }
    })

    /*
     * Collections
     */

    // TrackList: Collection of tracks
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
                    "queue_item": this.model.get('queueEntryId'),
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
          app.S.removeFromMySavedTracks([this.model.get("trackKey")])
              .then(() => {
                this.isFavorited = false;
                $('#favorite-button').removeClass("was_favorited").addClass("not_favorited");
                chat.sendMessage("unfavorited this track");
              })
              .catch((err) => {console.log('Failed to unfavorite ' + this.model.get("trackKey"), err)})
        },

        favoriteCurrentlyPlaying: function() {
          app.S.addToMySavedTracks([this.model.get("trackKey")])
              .then(() => {
                this.isFavorited = true;
                $('#favorite-button').removeClass("not_favorited").addClass("was_favorited");
                chat.sendMessage("favorited this track");
              })
              .catch((err) => {console.log('Failed to favorite ' + this.model.get("trackKey"), err)})
        },
    });

    // Model = app.playState (Player)
    app.NowPlayingView = Backbone.View.extend({
      el: '#now-playing',

      template: _.template($('#now-playing-template').html()),

      events: {
        'click .mute': '_handleMuteClick',
        'click .music': '_handleSpeakerClick'
      },

      initialize: function() {
        let self = this
        setInterval(() => { self.updatePlayerState() }, 1000);
        self.updatePlayerState();
        this.render()
      },

       updatePlayerState: function() {
        var player = this.model.get('spotifyPlayer');
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
          var player = this.model.get('spotifyPlayer');
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
        if (this.model.get('playingTrack') && this.model.get('position')) {
          console.log("Jumping player to track '"+this.model.get('playingTrack')+"' @ "+this.model.get('position')+"s");
        }
      },

      initChildModels: function() {
        this.skipButton = new app.SkipButton({
            model: this.model
        });

        app.S.containsMySavedTracks([this.model.get('trackKey')])
            .then((favResults) => {
              console.log('Track is favorite: ', favResults[0]);
              this.favoriteButton = new app.FavoriteButton({
                isFavorited: favResults[0],
                model: this.model
              });
            })
            .catch((err) => {
              console.log('Error checking if track is favorite: ', err);
              this.favoriteButton = new app.FavoriteButton({
                isFavorited: false,
                model: this.model
              });
            })
      },

      setColor: function(color) {
        $('#wrap').css('background', color)
      },

      render: function() {
        var self = this;
        if (this.model.get('spotifyPlayer') && this.model.get('trackKey')) {
          console.log("Track Key: ", this.model.get('trackKey'));
          getTrack(this.model.get('trackKey'), (error, track) => {
            // Set up the background color
            window.Vibrant.from(track.album.images[0].url).getPalette(function(err, palette) {
                if (palette) {
                    self.setColor(palette.DarkVibrant.getHex())
                }
            });
            var data = _.extend({
                track: {
                    bigIcon: track.album.images[0].url,
                    name: track.name,
                    url: track.shortUrl,
                    album: track.album.name,
                    artist: track.artists.map(a => a.name).join(", ")
                },
                addedBy: self.model.get('userKey')
            });
            self.play();
            self.$el.html(self.template(data));
            self.$el.show();
            self.initChildModels();
          })
        } else {
          if (this.model.get('spotifyPlayer') !== undefined) {
            app.S.pause(console.log)
          }
          this.setColor("#008fd5");
          this.$el.hide();
        }
        return this;
      },

      play: function() {
          if (this.model.get('trackKey')) {
              getTrack(this.model.get('trackKey'), (error, track) => {
                  // check the current active device so that we don't steal playback if it has
                  // changed during the previous song
                this.getActiveDeviceId((activeDeviceId)=> {
                    let payload = {
                        uris: [track.uri],
                        position_ms: this.model.get("position") * 1000,
                    };

                    payload.device_id = activeDeviceId || this.model.get('localDeviceId');
                    console.log('Playing on device id: ', payload.device_id);
                    app.S.play(payload)
                })
              })
          }
      },

      getActiveDeviceId: function(callback) {
          app.S.getMyDevices((error, response) => {
              console.log('Getting devices...');
              if (error) {
                  console.error(`Received error: ${error}`)
              } else {
                  let activeDeviceIds = response.devices
                      .filter((device) => device.is_active)
                      .map(device => device.id);
                  if (activeDeviceIds.length) {
                    callback(activeDeviceIds[0]);
                  } else {
                      callback(undefined);
                  }
              }
          });
      },

      /**
       * Called when the client should listen to a remote player
       **/
      init: function() {
        this.model.on('change:trackKey', this._onPlayerTrackChange, this);
        this.model.on('change:localDeviceId', this.render, this);
      },

      _onPlayerTrackChange: function(model, value, options) {
        console.log(model)
        if (model.get('trackKey')) {
            this.render()
        } else {
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
      },

      downVote: function() {
        this.model.downVote();
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

    app.QueueView = Backbone.View.extend({
      el: '#queue',

      statsTemplate: _.template($('#stats-template').html()),

      initialize: function() {
        this.queueStats = $('#queue-stats');

        this.listenTo(this.model, 'add', this.addOne);
        this.listenTo(this.model, 'reset', this.addAll);
        this.listenTo(this.model, 'sort', this.addAll);
        this.listenTo(this.model, 'change', this.sortQueue);
        this.listenTo(this.model, 'all', this.render);
      },

      render: function() {
        if (this.model.length) {
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
        this.model.sort();
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

    receiveMessage = function(event) {
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

    // Initialization
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
      websocket.onmessage = receiveMessage

      app.S = new app.SpotifyAPI()
      app.S.setAccessToken(window.spotify_access_token)

      app.queue = new app.TrackList();
      app.playState = new app.Player();
      app.themeModel = new app.ThemeInfo();

      var queueView = new app.QueueView({
        model: app.queue
      });
      app.nowPlayingView = new app.NowPlayingView({
        model: app.playState,
      });
      var searchView = new app.SearchView();
      var playlistView = new app.PlaylistView();
      app.themeView = new app.ThemeView({model: app.themeModel});
      var skipButton = new app.SkipButton();

      app.nowPlayingView.init();

      // Initialize the state
      app.playState.setState(window.initial_player_state);
      app.queue.setQueue(window.initial_queue_state);
      chat.activeUsers.setUserList(window.initial_user_list_state);
      chat.messageHistory.setMessages(window.initial_messages_state);
      app.themeModel.setTheme(window.initial_theme_state);

      // Ping every 10 seconds
      setInterval(ping, 10000);
    });
})();
