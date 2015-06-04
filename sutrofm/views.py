import subprocess
import psutil
import os
import json

from django.conf import settings
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import redirect, render, render_to_response
from django.views.decorators.csrf import csrf_exempt
from django.views.generic.base import TemplateView
from firebase_token_generator import create_token
from ws4redis.publisher import RedisPublisher
from ws4redis.redis_store import RedisMessage


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
    return render_to_response('player-helper.html')


class UserChatView(TemplateView):
    template_name = 'user_chat.html'

    @csrf_exempt
    def dispatch(self, *args, **kwargs):
        return super(UserChatView, self).dispatch(*args, **kwargs)

    def post(self, request, *args, **kwargs):
        redis_publisher = RedisPublisher(facility='foobar', users=[request.POST.get('user')])
        message = RedisMessage(request.POST.get('message'))
        redis_publisher.publish_message(message)
        return HttpResponse('OK')

class BroadcastChatView(TemplateView):
    template_name = 'broadcast_chat.html'

    def get(self, request, *args, **kwargs):
        welcome = RedisMessage('Hello everybody')  # create a welcome message to be sent to everybody
        RedisPublisher(facility='foobar', broadcast=True).publish_message(welcome)
        return super(BroadcastChatView, self).get(request, *args, **kwargs)
