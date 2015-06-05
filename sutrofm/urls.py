from django.conf.urls import include, url
from django.contrib import admin
from django.contrib.auth import logout
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from sutrofm import views

import api_views


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
    url(r'^create-auth/', 'sutrofm.views.createauthtoken'),

    url(r'^api/parties', api_views.parties, name='parties'),
    url(r'^api/users/$', api_views.users, name='users'),
    url(r'^api/user/((?P<user_id>[0-9]+)/)', api_views.get_user_by_id),
]

urlpatterns += staticfiles_urlpatterns()
