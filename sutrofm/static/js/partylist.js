/*globals app, console, R, Backbone, rdioUserKey */

window.app = window.app || {};

app.currentUserKey = rdioUserKey;

app.Room = Backbone.Model.extend({
});

app.RoomList = Backbone.Collection.extend({
  model: app.Room,

  initialize: function() {
    var self = this;
    $.ajax({
      url: '/api/parties',
      success: function(response) {
        self.add(response.results);
      }
    });
  }
});

app.RoomView = Backbone.View.extend({
  tagName: 'li',

  template: _.template($('#room-template').html()),

  initialize: function(){
    this.listenTo(this.model, 'change:player', this.onPlayerChanged);
    this.listenTo(this.model, 'change:people', this.render);
  },

  onPlayerChanged: function(change) {
    var previousTrack = change.previousAttributes().player.playingTrack.trackKey;
    var newTrack = change.changedAttributes().player.playingTrack.trackKey;
    if (previousTrack != newTrack) {
      this.render();
    }
  },

  render: function() {
    var self = this;
    var roomName = this.model.get('name');

    var people = this.model.get('people');
    var population = _.reduce(people, function (memo, obj) {
      if (obj.is_online === true) {
        return memo + 1;
      }
      return memo;
    }, 0);

    if (population === 0) {
      // don't render empty rooms.
      self.$el.hide();
      return;
    }

    var populationStr = '';

    if (population === 0) {
      populationStr = 'Empty';
    } else if (population === 1) {
      populationStr = '1 person';
    } else {
      populationStr = population + ' people';
    }

    var data = _.extend({
      name: roomName,
      id: this.model.get('id'),
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
            extras: '-*,name,artist,icon400'
          },
          success: function(response) {
            var track = response.result[playingTrackKey];
            if (track) {
              var track_name = track.name;
              var artist = track.artist;
              data.nowPlaying = '"' + track_name + '" by ' + artist;
              data.icon = track.icon400;
              data.has_icon = 'has_icon';
            } else {
              data.nowPlaying = 'Something unknown';
              data.icon = '';
              data.has_icon = '';
            }
            self.$el.html(self.template(data));
            self.$el.show();
          },
          error: function(response) {
            console.log("Unable to get now playing info for room " + roomName);
          }
        });
      } else {
        data.nowPlaying = "silence";
        data.icon = '';
        data.has_icon = '';
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
    //this.listenTo(app.partyRooms, 'change', this.onListChanged);

    // and draw the initial rooms
    if (app.partyRooms.length === 0) {
      this.$el.html(_.template($("#spinner-template").html()));
    } else {
      this.redraw(app.partyRooms, {});
    }
  },

  drawRoom: function(model, collection, options) {
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
    this.redraw(app.partyRooms, {});
  }
});

R.ready(function() {
  app.partyRooms = new app.RoomList();
  var partyRoomListView = new app.PartyRoomListView();

  $('#create-room-button').click(function(e){
    e.preventDefault();
    var roomName = $('#room-name-input').val();
    var allowedChars = /^[A-Za-z0-9_\-]+$/;
    var matches = roomName.match(allowedChars);
    if (matches && matches[0] == roomName) {
      //we have a match

      // TODO check if the room existed before, give the user the option to reset it
      console.log("room name is valid");
      window.location = window.location.origin + '/p/' + roomName;
    } else {
      // TODO render this error in the dom
      alert("Invalid room name");
    }
  });
});
