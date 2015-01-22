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

    initialize: function() {
      var self = this;

      this.$menu = this.$('.dropdown-menu')
        .on('click', 'a', function(event) {
          event.preventDefault();
          var $target = $(event.currentTarget);
          var originalVote = {};
          originalVote[app.currentUserKey] = "like";
          app.queue.add({
            trackKey: $target.data('rdio-key'),
            userKey: app.currentUserKey,
            votes: originalVote
          });

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

    search: function(query) {
      var self = this;

      if (this.request) {
        this.request.abort();
        this.request = null;
      }

      this.query = query;
      this.request = R.request({
        method: 'search',
        content: {
          query: query,
          types: 'Track',
          extras: '-*,key,icon,name,artist,duration',
          count: 10
        },
        success: function(data) {
          if (self.query != query) {
            return;
          }

          self.request = null;
          self.query = null;

          self.$menu
            .empty()
            .unbind('clickoutside')
            .bind('clickoutside', function() {
              self.close();
              self.$input.val('');
            })
            .show();

          _.each(data.result.results, function(v, i) {
            var durationMins = Math.floor(v['duration'] / 60);
            var durationSecs = v['duration'] % 60;
            if (durationSecs.length < 2)
              durationSecs = "0" + durationSecs;
            v['formattedDuration'] = durationMins + ":" + durationSecs;
            var html = $.trim(self.resultTemplate(v));
            self.$menu.append(html);
          });
        },
        error: function(data) {
          self.request = null;
          if (data.status != 'abort') {
            // TODO: Inform the user
            /*globals console */
            console.error('Search for ' + query + ' gives error: ' + data.message);
          }
        }
      });

    }
  });

})();