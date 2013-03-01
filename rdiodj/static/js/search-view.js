/*globals app, Backbone, R */

(function() {

  app.SearchView = Backbone.View.extend({
    el: '#play-track-form',
    resultTemplate: _.template($('#search-result-template').html()),

    initialize: function() {
      var self = this;

      this.$menu = this.$('.dropdown-menu')
        .on('click', 'a', function(event) {
          event.preventDefault();
          var $target = $(event.currentTarget);
          app.queue.add({
            trackKey: $target.data('rdio-key'),
            userKey: app.currentUserKey
          });

          self.close();
        });

      var $input = $('#track-key-input')
        .val('')
        .keypress(function() {
          _.delay(function() {
            var val = $input.val();
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
      }

      this.$menu.hide();
    },

    search: function(query) {
      var self = this;

      if (this.request) {
        this.request.abort();
        this.request = null;
      }

      this.request = R.request({
        method: 'search',
        content: {
          query: query,
          types: 'Track',
          extras: '-*,key,icon,name,artist',
          count: 10
        },
        success: function(data) {
          self.request = null;

          self.$menu
            .empty()
            .show();

          _.each(data.result.results, function(v, i) {
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