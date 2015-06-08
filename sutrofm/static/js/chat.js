var chat = chat || {};
chat.User = Backbone.Model.extend({});
chat.firebasePeopleRef = new Firebase(firebaseRootUrl + '/people');
chat.firebaseMessagesRef = new Firebase(firebaseRootUrl + '/messages');
chat.UserList = Backbone.Firebase.Collection.extend({
	model: chat.User,
	// pass the ref here instead of string so we can listen for disconnect.
	firebase: chat.firebasePeopleRef,
	getOnlineUsers: function() {
		return this.filter(function(user) {
			return user.get('isOnline');
		});
	}
});
chat.activeUsers = new chat.UserList();
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
		if (model.get('isOnline')) {
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
chat.MessageHistoryList = Backbone.Firebase.Collection.extend({
	model: chat.Message,
	firebase: chat.firebaseMessagesRef
});
chat.UserMessageView = Backbone.View.extend({
	tagName: 'li',
	template: _.template($('#chat-user-message-template').html()),
	render: function() {
		var user = chat.activeUsers.get(this.model.get('userKey'));
		// Strip all tags from the message. Regex explanation: http://regexr.com/3b0rq
		var message = this.model.get('message').replace(/<(?:.|\n)*?>/gm, '');
		if (user) {
			icon = user.attributes.icon;
		} else {
			icon = '';
		}
		var data = {
			fullName: this.model.get('fullName'),
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
			iconUrl: this.model.get('iconUrl'),
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
		var messageType = model.get('type');
		if (messageType == 'User') {
			var messageView = new chat.UserMessageView({
				model: model
			});
			this.$el.append(messageView.render().el);
			this.el.parentElement.scrollTop = this.el.parentElement.scrollHeight;
		} else if (messageType == 'NewTrack') {
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
	var userKey = R.currentUser.get('key');
	// add current user to activeUsers list, if they're not already
	var user = chat.activeUsers.get(userKey);
	if (user === undefined) {
		chat.activeUsers.add({
			id: userKey,
			isOnline: true,
			icon: R.currentUser.get('icon'),
			fullName: R.currentUser.get('firstName') + ' ' + R.currentUser.get('lastName')
		});
		console.log("added user ", chat.activeUsers.get(userKey), " to chat");
	}
	var isOnlineRef = chat.activeUsers.firebase.child(userKey).child('isOnline');
	console.log('online presence:', isOnlineRef.toString());
	// Mark yourself as offline on disconnect
	isOnlineRef.onDisconnect().set(false);
	// Mark yourself as online
	isOnlineRef.set(true);
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
	chat.messageHistory = new chat.MessageHistoryList();
	var chatView = new chat.MessagesView();
});
chat.sendMessage = function(message) {
	var fullName = chat.currentUser.get('firstName') + ' ' + chat.currentUser.get('lastName');
	var messageData = {
		type: 'User',
		fullName: fullName,
		userKey: chat.currentUser.get('key'),
		message: message,
		timestamp: (new Date()).toISOString()
	};
	chat.messageHistory.add(messageData);
};