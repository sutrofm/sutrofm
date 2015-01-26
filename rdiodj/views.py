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

def home(request):
    c = RequestContext(request, {
        # Something good
    })
    return render_to_response('index.html', c)

def ajax(request):
    data = {
  "albums": [
    {
      "key": "a5154181",
      "icon": "http://rdio3img-a.akamaihd.net/album/5/8/5/00000000004ea585/2/square-200.jpg"
    },
    {
      "key": "a5178363",
      "icon": "http://rdio1img-a.akamaihd.net/album/b/f/3/00000000004f03fb/2/square-200.jpg"
    },
    {
      "key": "a4621023",
      "icon": "http://img02.cdn2-rdio.com/album/f/d/2/00000000004682df/1/square-200.jpg"
    },
    {
      "key": "a1067012",
      "icon": "http://rdio1img-a.akamaihd.net/album/4/0/8/0000000000104804/5/square-200.jpg"
    },
    {
      "key": "a4583415",
      "icon": "http://rdio1img-a.akamaihd.net/album/7/f/f/000000000045eff7/2/square-200.jpg"
    },
    {
      "key": "a3450199",
      "icon": "http://rdio1img-a.akamaihd.net/album/7/5/5/000000000034a557/4/square-200.jpg"
    },
    {
      "key": "a1981009",
      "icon": "http://rdio1img-a.akamaihd.net/album/1/5/a/00000000001e3a51/5/square-200.jpg"
    },
    {
      "key": "a4550334",
      "icon": "http://rdio1img-a.akamaihd.net/album/e/b/e/0000000000456ebe/1/square-200.jpg"
    },
    {
      "key": "a3770804",
      "icon": "http://img00.cdn2-rdio.com/album/4/b/9/00000000003989b4/3/square-200.jpg"
    },
    {
      "key": "a5153931",
      "icon": "http://img02.cdn2-rdio.com/album/b/8/4/00000000004ea48b/1/square-200.jpg"
    },
    {
      "key": "a5177854",
      "icon": "http://rdio3img-a.akamaihd.net/album/e/f/1/00000000004f01fe/2/square-200.jpg"
    },
    {
      "key": "a4958619",
      "icon": "http://img00.cdn2-rdio.com/album/b/9/9/00000000004ba99b/2/square-200.jpg"
    },
    {
      "key": "a4962563",
      "icon": "http://img00.cdn2-rdio.com/album/3/0/9/00000000004bb903/1/square-200.jpg"
    },
    {
      "key": "a4803755",
      "icon": "http://img00.cdn2-rdio.com/album/b/a/c/0000000000494cab/6/square-200.jpg"
    },
    {
      "key": "a5133364",
      "icon": "http://img02.cdn2-rdio.com/album/4/3/4/00000000004e5434/1/square-200.jpg"
    },
    {
      "key": "a4835080",
      "icon": "http://img02.cdn2-rdio.com/album/8/0/7/000000000049c708/1/square-200.jpg"
    },
    {
      "key": "a5143471",
      "icon": "http://img00.cdn2-rdio.com/album/f/a/b/00000000004e7baf/1/square-200.jpg"
    },
    {
      "key": "a1027016",
      "icon": "http://rdio1img-a.akamaihd.net/album/8/c/b/00000000000fabc8/3/square-200.jpg"
    },
    {
      "key": "a3751317",
      "icon": "http://rdio3img-a.akamaihd.net/album/5/9/d/0000000000393d95/3/square-200.jpg"
    },
    {
      "key": "a5135870",
      "icon": "http://img00.cdn2-rdio.com/album/e/f/d/00000000004e5dfe/1/square-200.jpg"
    },
    {
      "key": "a306417",
      "icon": "http://img00.cdn2-rdio.com/album/1/f/c/000000000004acf1/6/square-200.jpg"
    },
    {
      "key": "a632489",
      "icon": "http://img00.cdn2-rdio.com/album/9/a/6/000000000009a6a9/1/square-200.jpg"
    },
    {
      "key": "a5093530",
      "icon": "http://img02.cdn2-rdio.com/album/a/9/8/00000000004db89a/3/square-200.jpg"
    },
    {
      "key": "a211632",
      "icon": "http://img02.cdn2-rdio.com/album/0/b/a/0000000000033ab0/square-200.jpg"
    },
    {
      "key": "a2142998",
      "icon": "http://img02.cdn2-rdio.com/album/6/1/3/000000000020b316/5/square-200.jpg"
    },
    {
      "key": "a3425579",
      "icon": "http://rdio3img-a.akamaihd.net/album/b/2/5/000000000034452b/3/square-200.jpg"
    },
    {
      "key": "a5165837",
      "icon": "http://rdio3img-a.akamaihd.net/album/d/0/3/00000000004ed30d/3/square-200.jpg"
    },
    {
      "key": "a4583460",
      "icon": "http://rdio1img-a.akamaihd.net/album/4/2/0/000000000045f024/1/square-200.jpg"
    },
    {
      "key": "a4929232",
      "icon": "http://img00.cdn2-rdio.com/album/0/d/6/00000000004b36d0/2/square-200.jpg"
    },
    {
      "key": "a3793586",
      "icon": "http://img00.cdn2-rdio.com/album/2/b/2/000000000039e2b2/2/square-200.jpg"
    },
    {
      "key": "a5138022",
      "icon": "http://rdio1img-a.akamaihd.net/album/6/6/6/00000000004e6666/1/square-200.jpg"
    },
    {
      "key": "a2766867",
      "icon": "http://rdio1img-a.akamaihd.net/album/3/1/8/00000000002a3813/2/square-200.jpg"
    },
    {
      "key": "a2161560",
      "icon": "http://img02.cdn2-rdio.com/album/8/9/b/000000000020fb98/3/square-200.jpg"
    },
    {
      "key": "a4814042",
      "icon": "http://rdio3img-a.akamaihd.net/album/a/d/4/00000000004974da/2/square-200.jpg"
    },
    {
      "key": "a3292131",
      "icon": "http://img02.cdn2-rdio.com/album/3/e/b/0000000000323be3/3/square-200.jpg"
    },
    {
      "key": "a4853535",
      "icon": "http://rdio1img-a.akamaihd.net/album/f/1/f/00000000004a0f1f/3/square-200.jpg"
    },
    {
      "key": "a2145065",
      "icon": "http://rdio3img-a.akamaihd.net/album/9/2/b/000000000020bb29/6/square-200.jpg"
    },
    {
      "key": "a259553",
      "icon": "http://img02.cdn2-rdio.com/album/1/e/5/000000000003f5e1/2/square-200.jpg"
    },
    {
      "key": "a3803878",
      "icon": "http://rdio3img-a.akamaihd.net/album/6/e/a/00000000003a0ae6/2/square-200.jpg"
    },
    {
      "key": "a4862964",
      "icon": "http://img02.cdn2-rdio.com/album/4/f/3/00000000004a33f4/1/square-200.jpg"
    },
    {
      "key": "a204574",
      "icon": "http://img00.cdn2-rdio.com/album/e/1/f/0000000000031f1e/square-200.jpg"
    },
    {
      "key": "a4995554",
      "icon": "http://img00.cdn2-rdio.com/album/2/e/9/00000000004c39e2/1/square-200.jpg"
    },
    {
      "key": "a4339336",
      "icon": "http://rdio3img-a.akamaihd.net/album/8/8/6/0000000000423688/3/square-200.jpg"
    },
    {
      "key": "a1134273",
      "icon": "http://img00.cdn2-rdio.com/album/1/c/e/0000000000114ec1/square-200.jpg"
    },
    {
      "key": "a4311750",
      "icon": "http://img02.cdn2-rdio.com/album/6/c/a/000000000041cac6/1/square-200.jpg"
    },
    {
      "key": "a4325668",
      "icon": "http://img00.cdn2-rdio.com/album/4/2/1/0000000000420124/1/square-200.jpg"
    },
    {
      "key": "a5070031",
      "icon": "http://rdio3img-a.akamaihd.net/album/f/c/c/00000000004d5ccf/1/square-200.jpg"
    },
    {
      "key": "a5138369",
      "icon": "http://img00.cdn2-rdio.com/album/1/c/7/00000000004e67c1/2/square-200.jpg"
    },
    {
      "key": "a3653028",
      "icon": "http://rdio1img-a.akamaihd.net/album/4/a/d/000000000037bda4/2/square-200.jpg"
    },
    {
      "key": "a4971455",
      "icon": "http://img02.cdn2-rdio.com/album/f/b/b/00000000004bdbbf/1/square-200.jpg"
    }
  ]
}

    return HttpResponse(json.dumps(data), content_type = "application/json")

def make_room_daemon(room_name):
  child_processes = psutil.Process(os.getpid()).get_children()
  for process in child_processes:
    try:
      if process.cmdline()[-1] == room_name:
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
