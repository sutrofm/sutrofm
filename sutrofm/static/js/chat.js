var chat = chat || {};

chat.User = Backbone.Model.extend({});

chat.Message = Backbone.Model.extend({});

chat.RedisUserList = Backbone.Collection.extend({
    model: chat.User,
    setUserList: function(data) {
      console.log('Updating user list');
      var self = this;
      user_keys = data.map(function(d) {
        return d['id'];
      });

      var user_list = data.map(function(value) {
        return new chat.User(value);
      });
      self.update(user_list);
    }
});

chat.RedisMessageHistoryList = Backbone.Collection.extend({
  model: chat.Message,
  createMessage: function(payload) {
    var dict = {
      'message': payload['text'],
      'messageType': payload['message_type']
    };
    switch (dict['messageType']) {
      case 'chat':
        dict['user_id'] = payload['user_id'];
      break;

      case 'new_track':
        dict['trackKey'] = payload['track_key'];
        dict['trackUrl'] = payload['track_url'];
        dict['icon'] = payload['icon_url'];
        dict['artist'] = payload['track_artist'];
        dict['title'] = payload['track_title'];
      break;
    }
    return new chat.Message(dict);
  },
  setMessages: function(messages) {
    // Gets a list from the API
    var self = this;
    var message_list = messages.map(function(value) {
      return self.createMessage(value);
    });
    this.update(message_list);
  },
  addMessage: function(value) {
    this.add(this.createMessage(value));
  }
});

chat.UserView = Backbone.View.extend({
  tagName: 'li',
  template: _.template($('#user-presence-template').html()),
  initialize: function() {
    this.listenTo(this.model, 'change', this.render);
    this.listenTo(this.model, 'remove', this.remove);
  },
  render: function() {
    var self = this;
    if (!this.model.get('is_active')) {
   	  return this;
    }
    var data = _.extend({
      'display_name': self.model.get('display_name'),
      'user_url': self.model.get('user_url'),
      'icon': self.model.get('icon')
    });
    self.$el.html(self.template(data));
    self.$el.show();
    return this;
  }
});

chat.UserListView = Backbone.View.extend({
  el: '#user-list',
  initialize: function() {
  	this._current_users = [];
    this.presenceStats = $('#presence-stats');
    // listen to when new users are added
    this.listenTo(chat.activeUsers, 'add', this.onListChanged);
    // and to when users change from online to offline
    this.listenTo(chat.activeUsers, 'change', this.onListChanged);
    //probably should render the activeUsers  on init so we have a starting point too.
    this.redraw(chat.activeUsers, {});
  },
  drawUser: function(model, collection, options) {
    if (model.get('is_active')) {
      var view = new chat.UserView({
        model: model
      });
      this.$el.append(view.render().el);
    }
  },
  redraw: function(collection, options) {
  	var activeUsers = collection.filter(function(user) {return user.get('is_active');});
  	activeUsers = activeUsers.map(function(user) {return user.get('id');});
  	if (_.difference(this._current_users, activeUsers).length || _.difference(activeUsers, this._current_users).length) {
      this.$el.empty();
      collection.each(this.drawUser, this);
      this._current_users = activeUsers;
    };
  },
  onListChanged: function(model, options) {
    // this is inefficient, but we don't have another hook to the dom element.
    this.redraw(chat.activeUsers, {});
  }
}); /* chat messages! */


chat.UserMessageView = Backbone.View.extend({
  tagName: 'li',
  template: _.template($('#chat-user-message-template').html()),
  render: function() {
    var users = chat.activeUsers.where({'id': this.model.get('user_id')});
    if (!users) {
      return this;
    }
    var user = users[0];
    // Strip all tags from the message. Regex explanation: http://regexr.com/3b0rq
    var message = this.model.get('message').replace(/<(?:.|\n)*?>/gm, '');
    if (user) {
      icon = user.attributes.icon;
      display_name = user.get('display_name');
    } else {
      icon = '';
      display_name = '';
    }
    var data = {
      display_name: display_name,
      icon: icon
    };
    this.$el.html(this.template(data));
    // Replace any urls in the message with anchor markup.
    // Options set are target="_blank", truncate link text, do not link email or phone
    message = Autolinker.link(message, { newWindow: true, truncate: 30, email: false, phone: false, });
    // Be careful in the future. Using html() instead of text() will allow a lot more to be passed through.
    this.$el.find('.chat-message').html(message);
    this.$el.show();
    return this;
  }
});

chat.NewTrackMessageView = Backbone.View.extend({
  tagName: 'li',
  template: _.template($('#chat-new-track-template').html()),
  render: function() {
    var data = {
      title: this.model.get('title'),
      artist: this.model.get('artist'),
      icon: this.model.get('icon'),
      trackUrl: this.model.get('trackUrl'),
      trackKey: this.model.get('trackKey')
    };
    this.$el.html(this.template(data));
    this.$el.show();
    return this;
  }
});

chat.MessagesView = Backbone.View.extend({
  el: '.chat-messages',
  initialize: function() {
    // there's probably a better way to do this with inheritance...
    this.listenTo(chat.messageHistory, 'add', this.onMessageAdded);
  },
  onMessageAdded: function(model, options) {
    var messageType = model.get('messageType');
    if (messageType == 'chat') {
      var messageView = new chat.UserMessageView({
        model: model
      });
      this.$el.append(messageView.render().el);
      this.el.parentElement.scrollTop = this.el.parentElement.scrollHeight;
    } else if (messageType == 'new_track') {
      if (model.get('trackKey')) {
        var trackView = new chat.NewTrackMessageView({
          model: model
        });
        this.$el.append(trackView.render().el);
        this.el.parentElement.scrollTop = this.el.parentElement.scrollHeight;
      }
    }
  }
});

$(function() {
  chat.activeUsers = new chat.RedisUserList();

  chat.currentUser = window.current_user
  var user_key = chat.currentUser["id"]
  // add current user to activeUsers list, if they're not already
  var user = chat.activeUsers.get(user_key);
  if (user === undefined) {
    chat.activeUsers.add({
      id: user_key,
      is_active: true,
      icon: chat.currentUser['icon'],
      display_name: chat.currentUser["display_name"]
    });
  }

  // draw user list view (after marking yourself as online)
  var userListView = new chat.UserListView();
  // Set up chat
  // user chat entry
  var chatEntryText = $('.chat-entry-text');
  chatEntryText.keypress(function(e) {
    if (e.keyCode == 13) { // listen for enter key
      var message = chatEntryText.val();
      chat.sendMessage(message);
      chatEntryText.val('');
    }
  });

  // we set up track change messages in sutrofm.js
  chat.messageHistory = new chat.RedisMessageHistoryList();
  var chatView = new chat.MessagesView();
});

chat.sendMessage = function(text) {
  $.ajax({
    'url': '/api/v2/chat_messages/',
    'method': 'POST',
    'data': {
      messageType: 'chat',
      user: chat.currentUser["id"],
      message: text,
      party: window.roomId
    }
  });
};
