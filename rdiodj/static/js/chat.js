var chat = chat || {};

chat.User = Backbone.Model.extend({

});

chat.firebaseRef = new Firebase(firebaseRootUrl + '/room/people');

chat.UserList = Backbone.Firebase.Collection.extend({
  model: chat.User,

  firebase: chat.firebaseRef, // pass the ref here instead of string so we can listen for disconnect.

  initialize: function() {
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

    this.listenTo(chat.presenceList, 'all', this.render);
  }

});


var connectedRef = new Firebase(firebaseRootUrl + '/.info/connected');

R.ready(function() {
  var userName = R.currentUser.get('vanityName');
  var userIcon= R.currentUser.get('icon');

  var userListView = new chat.UserListView();


  // add current user to chat list, if they're not already
  //
  var exists = chat.presenceList.any(function(user) {
    return user.get('vanityName') == userName;
  });
  console.log('user has been here before? ', exists);
  if (!exists) {
    chat.presenceList.add({
      vanityName: userName,
      iconSrc: userIcon,
      presenceStatus: 'offline'
    });
  }

  connectedRef.on('value', function(isOnline) {
    var user = chat.presenceList.find(function(user) {
      return user.get('vanityName') == userName;
    });

    console.log('user changed... ', user);

    if (isOnline.val()) {
      console.log(userName + " is online!");
      user.set('presenceStatus', 'online');
    } else {
      user.set('presenceStatus', 'offline');
    }
  });

  chat.firebaseRef.onDisconnect(function() {
    var user = chat.presenceList.find(function(user) {
      return user.get('vanityName') == userName;
    });

    user.set('presenceStatus', 'offline');
  });
});

