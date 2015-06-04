from django.conf import settings
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
import json
from django.http import HttpResponse

import subprocess
import psutil
import os
from firebase_token_generator import create_token


def home(request):
    context = {
        # Something good
        'body_class': 'home'
    }
    return render(request, 'index.html', context)

def createauthtoken(request):
    rdio_user_key = request.GET.get('userKey')
    if rdio_user_key:
        custom_data = {'rdio_user_key': rdio_user_key}
        options = {'debug': settings.DEBUG}
        firebase_token = create_token(settings.FIREBASE_TOKEN, custom_data, options)
        response = { "token": firebase_token }
    else:
        response = {"error": "userKey is a required GET param"}

    return HttpResponse(json.dumps(response), content_type="application/json")

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
    context = {
        'firebase_url': "%s/%s" % (settings.FIREBASE_URL, room_name),
        'room_name': room_name,
        'body_class': 'party'
    }
    make_room_daemon(room_name)
    return render(request, 'party.html', context)


def parties(request):
    context = {
        'firebase_url': "%s/" % (settings.FIREBASE_URL,),
        'body_class': 'parties'
    }
    return render(request, 'partylist.html', context)


def sign_out(request):
    logout(request)
    return redirect('/')


def player_helper(request):
    return render(request, 'player-helper.html')
