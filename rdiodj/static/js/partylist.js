/*globals app, console, R, Backbone, Firebase, rdioUserKey, firebaseToken, firebaseRootUrl, firebaseRef */

window.app = window.app || {};

app.currentUserKey = rdioUserKey;
app.firebaseUrl = firebaseRootUrl;

app.Room = Backbone.Model.extend({
});

app.RoomList = Backbone.Firebase.Collection.extend({
  model: app.Room,

  firebase: app.firebaseUrl
});

app.partyRooms = new app.RoomList();

app.RoomView = Backbone.View.extend({
  tagName: 'li',

  template: _.template($('#room-template').html()),

  initialize: function(){
    this.listenTo(this.model, 'change', this.render);
  },

  render: function() {
    var self = this;
    var roomName = this.model.get('id');

    var people = this.model.get('people');
    var population = _.reduce(people, function (memo, obj) {
      if (obj.isOnline === true) {
        return memo + 1;
      }
      return memo;
    }, 0);

    if (population === 0) {
      // don't render empty rooms.
      return;
    }

    var populationStr = '';

    if (population === 0) {
      populationStr = 'No one is';
    } else if (population === 1) {
      populationStr = '1 person is';
    } else {
      populationStr = population + ' people are';
    }

    var data = _.extend({
      name: roomName,
      population: populationStr
    });

    var player = this.model.get('player');
    if (player) {
      if (player.playingTrack) {
        var playingTrackKey = player.playingTrack.trackKey;
        R.request({
          method: 'get',
          content: {
            keys: playingTrackKey,
            extras: '-*,name,artist'
          },
          success: function(response) {
            var track = response.result[playingTrackKey].name;
            var artist = response.result[playingTrackKey].artist;
            data.nowPlaying = '"' + track + '" by ' + artist;
            self.$el.html(self.template(data));
            self.$el.show();
          },
          error: function(response) {
            console.log("Unable to get now playing info for room " + roomName);
          }
        });
      } else {
        data.nowPlaying = "silence";
        this.$el.html(this.template(data));
        this.$el.show();
      }
    } else {
      this.$el.hide();
    }
    return this;
  },
});

app.PartyRoomListView = Backbone.View.extend({
  el: '#party-list',

  initialize: function() {
    // listen for changes
    this.listenTo(app.partyRooms, 'add', this.onListChanged);
    this.listenTo(app.partyRooms, 'change', this.onListChanged);

    // and draw the initial rooms
    this.redraw(app.partyRooms, {});
  },

  drawRoom: function(model, collection, options) {
    console.log("should draw party room");
    var view = new app.RoomView({model: model});
    var rendered = view.render();
    if (rendered) {
      // empty rooms will return undefined and not be rendered.
      this.$el.append(rendered.el);
    }
  },

  redraw: function(collection, options) {
    this.$el.empty();
    collection.each(this.drawRoom, this);
  },

  onListChanged: function(model, options) {
    console.log("party room list changed with mode: ", model);
    this.redraw(app.partyRooms, {});
  }
});

R.ready(function() {
  firebaseRef.auth(firebaseToken, function(error) {
    if (error) {
      console.log('Login Failed!', error);
    } else {
      console.log('Login Succeeded!');

      var partyRoomListView = new app.PartyRoomListView();
    }
  });
});
