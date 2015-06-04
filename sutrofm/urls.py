from django.conf.urls import patterns, include, url
from django.contrib import admin
from django.contrib.staticfiles.urls import staticfiles_urlpatterns


admin.autodiscover()


urlpatterns = patterns('',
    url(r'^$', 'sutrofm.views.home', name='index'),
    url(r'^p/((?P<room_name>[A-Za-z0-9\-_]+)/)?$', 'sutrofm.views.party', name='party'),
    url(r'^parties/$', 'sutrofm.views.parties', name='parties'),

    url(r'^sign-out/$', 'django.contrib.auth.views.logout', {'next_page': '/'}, name='sign-out'),

    url(r'^player/helper/', 'sutrofm.views.player_helper', name='player-helper'),

    url(r'^auth/', include('social_auth.urls')),

    url(r'^admin/doc/', include('django.contrib.admindocs.urls')),
    url(r'^admin/', include(admin.site.urls)),
    url(r'^create-auth/', 'sutrofm.views.createauthtoken')
)


urlpatterns += staticfiles_urlpatterns()
