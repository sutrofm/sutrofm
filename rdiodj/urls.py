from django.conf.urls import patterns, include, url
from django.contrib import admin
from django.contrib.staticfiles.urls import staticfiles_urlpatterns


admin.autodiscover()


urlpatterns = patterns('',
    url(r'^$', 'rdiodj.views.home', name='index'),
    url(r'^party/((?P<room_name>\w+)/)?$', 'rdiodj.views.party', name='party'),

    url(r'^sign-out/$', 'django.contrib.auth.views.logout', {'next_page': '/'}, name='sign-out'),

    url(r'^player/helper/', 'rdiodj.views.player_helper', name='player-helper'),

    url(r'^auth/', include('social_auth.urls')),

    url(r'^admin/doc/', include('django.contrib.admindocs.urls')),
    url(r'^admin/', include(admin.site.urls)),
)


urlpatterns += staticfiles_urlpatterns()
