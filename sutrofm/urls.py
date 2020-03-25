"""sutrofm URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import re_path, path, include

from sutrofm import views, api_views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.home, name='index'),
    path('parties', views.parties, name='parties'),
    path('social', include('social_django.urls', namespace='social')),
    path('player/helper', views.player_helper, name='player-helper'),
    path('auth/name', views.login),

    path('api/parties', api_views.parties, name='api_parties'),
    re_path(r'^api/party/(?P<party_id>[A-Za-z0-9\-_]+)/?$', api_views.get_party_by_id),
    re_path(r'^api/party/(?P<party_id>[A-Za-z0-9\-_]+)/theme?$', api_views.get_theme),
    re_path(r'^api/party/(?P<party_id>[A-Za-z0-9\-_]+)/theme/set?$', api_views.set_theme),
    re_path(r'^api/party/(?P<party_id>[A-Za-z0-9\-_]+)/vote_to_skip$', api_views.vote_to_skip),
    re_path(r'^api/party/(?P<party_id>[A-Za-z0-9\-_]+)/queue$', api_views.get_party_queue),
    re_path(r'^api/party/(?P<party_id>[A-Za-z0-9\-_]+)/queue/upvote$', api_views.upvote),
    re_path(r'^api/party/(?P<party_id>[A-Za-z0-9\-_]+)/queue/downvote$', api_views.downvote),
    re_path(r'^api/party/(?P<party_id>[A-Za-z0-9\-_]+)/queue/add$', api_views.add_to_queue),
    re_path(r'^api/party/(?P<party_id>[A-Za-z0-9\-_]+)/queue/remove$', api_views.remove_from_queue),
    re_path(r'^api/party/(?P<party_id>[A-Za-z0-9\-_]+)/users$', api_views.get_party_users),
    re_path(r'^api/party/(?P<party_id>[A-Za-z0-9\-_]+)/messages/?$', api_views.messages, name='messages'),
    re_path(r'^api/party/(?P<party_id>[A-Za-z0-9\-_]+)/ping/?$', api_views.ping_party),

    path('api/users', api_views.users, name='api_users'),
    re_path(r'^api/user/((?P<user_id>[A-Za-z0-9]+)/)', api_views.get_user_by_id),


    re_path(r'^p/((?P<room_name>[A-Za-z0-9\-_]+)/)?$', views.party, name='party'),
]
