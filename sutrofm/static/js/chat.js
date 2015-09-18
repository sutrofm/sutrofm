var chat = chat || {};
chat.User = Backbone.Model.extend({});
chat.RedisUserList = Backbone.Collection.extend({
    model: chat.User,
    setUserList: function(data) {
      var self = this;
      user_keys = data.map(function(d) {
        return d['rdio_key']
      });

      var user_list = data.map(function(value) {
        return new chat.User(value);
      });
      self.update(user_list);
    }
})
chat.activeUsers = new chat.RedisUserList();
chat.UserView = Backbone.View.extend({
	tagName: 'li',
	template: _.template($('#user-presence-template').html()),
	initialize: function() {
		this.listenTo(this.model, 'change', this.render);
		this.listenTo(this.model, 'remove', this.remove);
	},
	render: function() {
		var self = this;
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
		// listen to when new users are added
		this.listenTo(chat.activeUsers, 'add', this.onListChanged);
		// and to when users change from online to offline
		this.listenTo(chat.activeUsers, 'change', this.onListChanged);
		//probably should render the activeUsers  on init so we have a starting point too.
		this.redraw(chat.activeUsers, {});
	},
	drawUser: function(model, collection, options) {
		if (model.get('is_online')) {
			console.log("rendering user: ", model);
			var view = new chat.UserView({
				model: model
			});
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
		this.redraw(chat.activeUsers, {});
	}
}); /* chat messages! */
chat.Message = Backbone.Model.extend({});
chat.RedisMessageHistoryList = Backbone.Collection.extend({
  model: chat.Message,
  createMessage: function(payload) {
    var dict = {
      'message': payload['text'],
      'messageType': payload['message_type']
    }
    switch (dict['messageType']) {
      case 'chat':
        dict['user_key'] = payload['user_key'];
        dict['display_name'] = payload['user_key'];
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
    debugger;
    this.add(this.createMessage(value));
  }
});

chat.UserMessageView = Backbone.View.extend({
	tagName: 'li',
	template: _.template($('#chat-user-message-template').html()),
	render: function() {
		var users = chat.activeUsers.where({'user_key': this.model.get('user_key')})
    if (!users) {
      return this;
    }
    var user = users[0];
    // Strip all tags from the message. Regex explanation: http://regexr.com/3b0rq
    var message = this.model.get('message').replace(/<(?:.|\n)*?>/gm, '');
    if (user) {
      icon = user.attributes.icon;
    } else {
      icon = '';
    }
    var data = {
      display_name: user.get('display_name'),
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
		console.log('chat view initialized');
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
			var trackView = new chat.NewTrackMessageView({
				model: model
			});
			this.$el.append(trackView.render().el);
			this.el.parentElement.scrollTop = this.el.parentElement.scrollHeight;
		}
	}
});
R.ready(function() {
	chat.currentUser = R.currentUser;
	var user_key = R.currentUser.get('key');
	// add current user to activeUsers list, if they're not already
	var user = chat.activeUsers.get(user_key);
	if (user === undefined) {
		chat.activeUsers.add({
			id: user_key,
			is_online: true,
			icon: R.currentUser.get('icon'),
			display_name: R.currentUser.get('firstName') + ' ' + R.currentUser.get('lastName')
		});
		console.log("added user ", chat.activeUsers.get(user_key), " to chat");
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
    'url': '/api/party/'+window.roomId+'/messages/',
    'method': 'POST',
    'data': {
      messageType: 'chat',
      user: chat.currentUser.get('key'),
      text: text
    }
  })
};
