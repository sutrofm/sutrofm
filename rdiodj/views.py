from django.conf import settings
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse
from django.http import HttpResponse
from django.shortcuts import render_to_response
from django.template import RequestContext


def home(request):
    c = RequestContext(request, {
        # Something good
    })
    return render_to_response('index.html', c)


@login_required
def party(request, room_name):
    if room_name is None:
        room_name = 'room'

    c = RequestContext(request, {
        'firebase_url': "%s/%s" % (settings.FIREBASE_URL, room_name)
    })
    return render_to_response('party.html', c)


def sign_out(request):
    response = logout(request, next_page=reverse('index'))
    return HttpResponse(response)


def player_helper(request):
    return render_to_response('player-helper.html',
                              {},
                              context_instance=RequestContext(request))
