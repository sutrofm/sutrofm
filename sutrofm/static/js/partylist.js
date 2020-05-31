/*globals app, console, R, Backbone */

window.app = window.app || {};

// app.currentUserKey = "{{user}}";

app.Room = Backbone.Model.extend({
});

app.RoomList = Backbone.Collection.extend({
  model: app.Room,

  initialize: function() {
    var self = this;
    $.ajax({
      url: '/api/v2/parties',
      success: function(response) {
        console.log(response);
        self.add(response);
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

    var users = this.model.get('users');
    // var population = _.reduce(people, function (memo, obj) {
    //   if (obj.is_active === true && obj.party_id === self.model.get('id')) {
    //     return memo + 1;
    //   }
    //   return memo;
    // }, 0);
    var population = users.length;

    // if (population === 0) {
    //   // don't render empty rooms.
    //   self.$el.hide();
    //   return;
    // }

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
      population: populationStr,
      theme: this.model.get('theme')
    });

    var playingItem = this.model.get('playing_item');
    if (playingItem) {
      var playingTrackKey = playingItem.identifier;
      // Request track data from spotify here
      if (true) {  // previously depedent upon a good response
        var track_name = playingItem.title;
        var artist = playingItem.artist_name;
        data.nowPlaying = '"' + track_name + '" by ' + artist;
        // data.icon = track.icon400;
        // data.has_icon = 'has_icon';
      } else {
        data.nowPlaying = 'Something unknown';
        data.icon = '';
      }
      self.$el.html(self.template(data));
      self.$el.show();
    } else {
      data.nowPlaying = "silence";
      data.icon = '';
      this.$el.html(this.template(data));
      this.$el.show();
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
  },

  close: function () {
    clearInterval(this.timer);
  }
});

$(function() {
  app.partyRooms = new app.RoomList();
  var partyRoomListView = new app.PartyRoomListView();
});
