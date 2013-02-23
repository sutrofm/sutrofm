from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ObjectDoesNotExist
from django.core.urlresolvers import reverse
from django.db.models import Q
from django.http import HttpResponse
from django.shortcuts import render_to_response
from django.template import RequestContext

import requests
from requests.auth import AuthBase

def home(request):
    c = RequestContext(request, {
        # Something good
    })
    return render_to_response('index.html', c)


def sign_out(request):
    response = logout(request, next_page=reverse('index'))
    return HttpResponse(response)
