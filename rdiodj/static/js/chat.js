var chat = chat || {};

chat.User = Backbone.Model.extend({

});

chat.firebasePeopleRef = new Firebase(firebaseRootUrl + '/people');
chat.firebaseMessagesRef = new Firebase(firebaseRootUrl + '/messages');

chat.UserList = Backbone.Firebase.Collection.extend({
  model: chat.User,

  firebase: chat.firebasePeopleRef // pass the ref here instead of string so we can listen for disconnect.
});

chat.presenceList = new chat.UserList();

chat.UserView = Backbone.View.extend({
  tagName: 'li',

  template: _.template($('#user-presence-template').html()),

  initialize: function() {
    this.listenTo(this.model, 'change', this.render);
    this.listenTo(this.model, 'remove', this.remove);
  },

  render: function() {
    var self = this;
    console.log("rendering user with icon at ", this.model.get('iconSrc'));

    R.request({
      method: 'get',
      content: {
        keys: this.model.get('id'),
        extras: 'shortUrl'
      },
      success: function(response) {
        var data = _.extend({
          'user': response.result[self.model.get('id')]
        });
        self.$el.html(self.template(data));
        self.$el.show();
      },
      error: function(response) {
        console.log('Unable to get user information for', self.model.get('id'));
      }
    });

    return this;
  }
});


chat.UserListView = Backbone.View.extend({
  el: '#user-list',

  initialize: function() {
    this.presenceStats = $('#presence-stats');

    this.listenTo(chat.presenceList, 'change', this.onListChanged);
    this.listenTo(chat.presenceList, 'all', this.render);

    //probably should render the presenceList on init so we have a starting point too.
    console.log("render all the users here?");
    this.redraw(chat.presenceList, {});
  },

  drawUser: function(model, collection, options) {
    if (model.get('isOnline')) {
      var view = new chat.UserView({ model: model });
      this.$el.append(view.render().el);
    }
  },

  redraw: function(collection, options) {
    this.$el.empty();
    collection.each(this.drawUser, this);
  },

  onListChanged: function(model, options) {
    console.log("list changed with model: ", model);
    // this is inefficient, but we don't have another hook to the dom element.
    this.redraw(chat.presenceList, {});
  }

});


R.ready(function() {
  var userKey = R.currentUser.get('key');
  var userListView = new chat.UserListView();

  // add current user to chat list, if they're not already
  var user = chat.presenceList.get(userKey);
  if (user === undefined) {
    chat.presenceList.add({
      id: userKey,
      isOnline: false
    });
  }

  var isOnlineRef = chat.presenceList.firebase.child(userKey).child('isOnline');
  console.log('online presence:', isOnlineRef.toString());

  // Mark yourself as offline on disconnect
  isOnlineRef.onDisconnect().set(false);

  // Mark yourself as online
  isOnlineRef.set(true);

  // Set up chat input


});
