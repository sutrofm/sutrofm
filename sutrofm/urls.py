from django.conf.urls import include, url
from django.contrib import admin
from django.contrib.auth import logout
from django.contrib.staticfiles.urls import staticfiles_urlpatterns

import api_views
from sutrofm import views


admin.autodiscover()

urlpatterns = [
  url(r'^$', views.home, name='index'),
  url(r'^p/((?P<room_name>[A-Za-z0-9\-_]+)/)?$', views.party, name='party'),
  url(r'^parties/$', views.parties, name='parties'),
  url(r'^sign-out/$', logout, {'next_page': '/'}, name='sign-out'),
  url(r'^player/helper/', views.player_helper, name='player-helper'),
  url(r'^auth/', include('social_auth.urls')),
  url(r'^admin/doc/', include('django.contrib.admindocs.urls')),
  url(r'^admin/', include(admin.site.urls)),

  url(r'^api/parties/$', api_views.parties, name='api_parties'),
  url(r'^api/party/(?P<party_id>[A-Za-z0-9\-_]+)/?$', api_views.get_party_by_id),
  url(r'^api/party/(?P<party_id>[A-Za-z0-9\-_]+)/theme?$', api_views.get_theme),
  url(r'^api/party/(?P<party_id>[A-Za-z0-9\-_]+)/theme/set?$', api_views.set_theme),
  url(r'^api/party/(?P<party_id>[A-Za-z0-9\-_]+)/vote_to_skip$', api_views.vote_to_skip),
  url(r'^api/party/(?P<party_id>[A-Za-z0-9\-_]+)/queue$', api_views.get_party_queue),
  url(r'^api/party/(?P<party_id>[A-Za-z0-9\-_]+)/queue/upvote$', api_views.upvote),
  url(r'^api/party/(?P<party_id>[A-Za-z0-9\-_]+)/queue/downvote$', api_views.downvote),
  url(r'^api/party/(?P<party_id>[A-Za-z0-9\-_]+)/queue/add$', api_views.add_to_queue),
  url(r'^api/party/(?P<party_id>[A-Za-z0-9\-_]+)/queue/remove$', api_views.remove_from_queue),
  url(r'^api/party/(?P<party_id>[A-Za-z0-9\-_]+)/users$', api_views.get_party_users),
  url(r'^api/party/(?P<party_id>[A-Za-z0-9\-_]+)/messages/?$', api_views.messages, name='messages'),

  url(r'^api/users/$', api_views.users, name='api_users'),
  url(r'^api/user/((?P<user_id>[A-Za-z0-9]+)/)', api_views.get_user_by_id),

  url(r'^api/ping/$', api_views.ping),
]

urlpatterns += staticfiles_urlpatterns()
