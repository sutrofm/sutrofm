from django.conf import settings
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse
from django.http import HttpResponse
from django.shortcuts import redirect, render_to_response
from django.template import RequestContext
import json
from django.http import HttpResponse

import subprocess
import psutil
import os
from firebase_token_generator import create_token

def home(request):
    c = RequestContext(request, {
        # Something good
    })
    return render_to_response('index.html', c)

def createauthtoken(request):
    response = None

    rdio_user_key = request.GET.get('userKey')
    if rdio_user_key:
        custom_data = {'rdio_user_key': rdio_user_key}
        options = {'debug': settings.DEBUG}
        firebase_token = create_token(settings.FIREBASE_TOKEN, custom_data, options)
        response = { "token": firebase_token }
    else:
        response = {"error": "userKey is a required GET param"}

    return HttpResponse(json.dumps(response), content_type = "application/json")

def make_room_daemon(room_name):
  child_processes = psutil.Process(os.getpid()).get_children()
  for process in child_processes:
    try:
      if process.cmdline() and len(process.cmdline()) > 0 and process.cmdline()[-1] == room_name:
        return
    except psutil.AccessDenied:
      pass
  directory = os.path.dirname(os.path.realpath(__file__))
  subprocess.Popen(["python", "%s/../manage.py" % directory, "master", room_name])


@login_required
def party(request, room_name):
    if room_name is None:
        return redirect('/p/rdio')

    c = RequestContext(request, {
        'firebase_url': "%s/%s" % (settings.FIREBASE_URL, room_name),
        'room_name': room_name
    })
    make_room_daemon(room_name)
    return render_to_response('party.html', c)


def parties(request):
    c = RequestContext(request, {
        'firebase_url': "%s/" % (settings.FIREBASE_URL,)
    })
    return render_to_response('partylist.html', c)


def sign_out(request):
    response = logout(request, next_page=reverse('index'))
    return HttpResponse(response)


def player_helper(request):
    return render_to_response('player-helper.html',
                              {},
                              context_instance=RequestContext(request))
