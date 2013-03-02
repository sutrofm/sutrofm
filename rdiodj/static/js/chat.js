var chat = chat || {};

chat.User = Backbone.Model.extend({

});

chat.firebaseRef = new Firebase(firebaseRootUrl + '/people');

chat.UserList = Backbone.Firebase.Collection.extend({
  model: chat.User,

  firebase: chat.firebaseRef // pass the ref here instead of string so we can listen for disconnect.
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
    console.log("rendering user with icon at ", this.model.get('iconSrc'));
    var data = _.extend({
      'name': this.model.get('vanityName'),
      'iconSrc': this.model.get('iconSrc')
    });
    this.$el.html(this.template(data));
    this.$el.show();
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
    if (model.get('presenceStatus') != 'offline') {
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
  var userName = R.currentUser.get('vanityName');
  var userIcon = R.currentUser.get('icon');
  var userKey = R.currentUser.get('key');

  var userListView = new chat.UserListView();


  // add current user to chat list, if they're not already
  var user = chat.presenceList.get(userKey);
  if (user === undefined) {
    chat.presenceList.add({
      id: userKey,
      vanityName: userName,
      iconSrc: userIcon,
      presenceStatus: 'offline'
    });
  }

  var presenceRef = chat.presenceList.firebase.child(userKey).child('presenceStatus');

  presenceRef.onDisconnect(function() {
    presenceRef.set('presenceStatus', 'offline');
  });

  // Mark yourself as online
  presenceRef.set('presenceStatus', 'online');

});
