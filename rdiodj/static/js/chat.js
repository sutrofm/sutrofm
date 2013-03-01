var chat = chat || {};

chat.User = Backbone.Model.extend({

});

chat.UserList = Backbone.Firebase.Collection.extend({
  model: chat.User,

  firebase: firebaseRootUrl + '/room/people'
});

chat.presenceList = new chat.UserList();

chat.UserView = Backbone.View.extend({
  tagName: 'li',

  template: _.template($('#user-presence-template').html()),

  initialize: function() {
    this.listenTo(this.model, 'change', this.render);
    this.listenTo(this.model, 'remove', this.remove);

  }
});


chat.OnlineUsersView = Backbone.View.extend({
  el: '#user-list',

  initialize: function() {
    this.presenceStats = $('#presence-stats');

    this.listenTo(chat.presenceList, 'add', this.addUser);
    this.listenTo(chat.presenceList, 'remove', this.removeUser);
    this.listenTo(chat.presenceList, 'all', this.render);
  },

  render: function() {
  },

  addUser: function(model, collection, options) {
    console.log('addUser', model, collection, options);
    var view = new chat.UserView({ model: model });
    this.$el.append(view.render().el);
  },

  removeUser: function(model, collection, options) {
  }
});


var connectedRef = new Firebase(firebaseRootUrl + '/.info/connected');

R.ready(function() {
  var userName = R.currentUser.get('vanityName');
  var userIcon= R.currentUser.get('icon');

  connectedRef.on('value', function(isOnline) {
    if (isOnline.val()) {
      console.log(userName + " is online!");
      chat.presenceList.add({
        vanityName: userName,
        iconSrc: userIcon
      });
    } else {
      console.log(currentUser + " is offline!");
      chat.presenceList.remove({
        vanityName: userName,
        iconSrc: userIcon
      });
    }
  });
});

