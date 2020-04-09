/*globals app, Backbone, R */

// TODO: 
//
// * Keyboard navigation for menu (arrows select, return chooses, escape dismisses)
// * Perhaps when you click away it should leave the search string in the box, and if you
//   click back, it should open the menu again

(function() {

  app.SearchView = Backbone.View.extend({
    el: '.track-input',
    resultTemplate: _.template($('#search-result-template').html()),

    enqueueTrack: function(trackKey) {
      $.ajax({
        'url': '/api/v2/queue_items/',
        'method': 'POST',
        'data': {
            'identifier': trackKey,
            'party': window.roomId,
        }
      })
    },

    initialize: function() {
      var self = this;

      this.$menu = this.$('.dropdown-menu')
        .on('click', 'a', function(event) {
          event.preventDefault();
          var $target = $(event.currentTarget);
          var originalVote = {};
          originalVote[app.currentUserKey] = "like";
          self.enqueueTrack($target.data('spotify-key'));

          self.close();
          self.$input.val('');
        });

      this.$input = $('#track-key-input')
        .val('')
        .keypress(function() {
          _.delay(function() {
            var val = self.$input.val();
            if (val) {
              self.search(val);
            } else {
              self.close();
            }
          });
        });
    },

    render: function() {
    },

    close: function() {
      if (this.request) {
        this.request.abort();
        this.request = null;
        this.query = null;
      }

      this.$menu.hide();
    },

    search: _.throttle(function(query) {
      var self = this;

      if (this.request) {
        this.request.abort();
        this.request = null;
      }

      this.query = query;
      this.request = app.S.searchTracks(query, {limit: 10}, (error, result) => {
        if (result) {
          self.$menu
            .empty()
            .unbind('clickoutside')
            .bind('clickoutside', function() {
              self.close();
              self.$input.val('');
            })
            .show();

          _.each(result.tracks.items, function(track, i) {
            let durationMS = track.duration_ms
            let durationMins = Math.floor(durationMS / 60 * 1000)
            let durationSecs = String(durationMins % 60)
            if (durationSecs.length < 2)
              durationSecs = "0" + durationSecs;
            let iconUrl = track.album.images ? track.album.images[0].url : ""
            let data = {
                key: track.id,
                name: track.name,
                artist: track.artists.map((a) => a.name).join(", "),
                formattedDuration: durationMins + ":" + durationSecs,
                icon: iconUrl
            }
            var html = $.trim(self.resultTemplate(data));
            self.$menu.append(html);
          });
        } else {
            console.warn("No result: ", error)
        }
      })
    }, 500)
  });

})();
