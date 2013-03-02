var chat = chat || {};

chat.User = Backbone.Model.extend({

});

chat.firebaseRef = new Firebase(firebaseRootUrl + '/room/people');

chat.UserList = Backbone.Firebase.Collection.extend({
  model: chat.User,

  firebase: chat.firebaseRef, // pass the ref here instead of string so we can listen for disconnect.

  listUpdated: function(updated) {
    if (updated.get('presenceStatus') == 'online') {
      var userView = new chat.UserView({ mode: updated });

    } else { // assume offline
      updated.remove();
    }
  }

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
    if (this.model.get('presenceStatus') == 'online') {
      console.log("rendering user with icon at ", this.model.get('iconSrc'));
      var data = _.extend({
        'name': this.model.get('vanityName'),
        'iconSrc': this.model.get('iconSrc')
      });
      this.$el.html(this.template(data));
      this.$el.show();
    } else {
      this.$el.hide();
    }
    return this;
  }
});


chat.UserListView = Backbone.View.extend({
  el: '#user-list',

  initialize: function() {
    this.presenceStats = $('#presence-stats');

    this.listenTo(chat.presenceList, 'change', this.redraw);
    this.listenTo(chat.presenceList, 'all', this.render);

    //probably should render the presenceList on init so we have a starting point too.
    console.log("render all the users here?");
    this.redraw(chat.presenceList, {});
  },

  listChanged: function(newItem) {
    console.log("list changed from the context of list view: ", newItem);
    console.log(arguments);
  },

  drawUser: function(model, collection, options) {
    var view = new chat.UserView({ model: model });
    this.$el.append(view.render().el);
  },

  redraw: function(collection, options) {
    this.$el.empty();
    collection.each(this.drawUser, this);
  }

});


var connectedRef = new Firebase(firebaseRootUrl + '/.info/connected');

R.ready(function() {
  var userName = R.currentUser.get('vanityName');
  var userIcon = R.currentUser.get('icon');
  var userKey = R.currentUser.get('key');

  var userListView = new chat.UserListView();


  // add current user to chat list, if they're not already
  //
  var exists = chat.presenceList.any(function(user) {
    return user.get('id') == userKey;
  });
  if (!exists) {
    chat.presenceList.add({
      id: userKey,
      vanityName: userName,
      iconSrc: userIcon,
      presenceStatus: 'offline'
    });
  }

  connectedRef.on('value', function(isOnline) {
    var user = chat.presenceList.find(function(user) {
      return user.get('id') == userKey;
    });

    if (isOnline.val()) {
      user.set('presenceStatus', 'online');
    } else {
      user.set('presenceStatus', 'offline');
    }
  });

  chat.firebaseRef.onDisconnect(function() {
    var user = chat.presenceList.find(function(user) {
      return user.get('id') == userKey;
    });

    user.set('presenceStatus', 'offline');
  });
});

