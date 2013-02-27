from django.core.urlresolvers import reverse
from django.template import Library


register = Library()


@register.simple_tag(takes_context=True)
def activelink(context, url):
    if 'request' in context:
        request_path = context['request'].path
        if request_path == reverse(url):
            return 'active'
    return ''
