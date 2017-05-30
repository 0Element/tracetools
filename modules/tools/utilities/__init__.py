from __future__ import unicode_literals

import json
import re

from django.conf import settings
from django.utils.html import strip_tags

from .helpers import send_queue_message


def get_ip_from_request(request):
    """
    Returns user's ip address from request.
    :param request: http request
    :type request: django.http.HttpRequest instance
    :return: ip address
    :rtype: str
    """
    if (settings.DEBUG or settings.TESTING_MODE) and hasattr(settings, "DEBUG_REMOTE_IP"):
        return settings.DEBUG_REMOTE_IP

    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')

    return ip


def get_user_agent_from_request(request):
    """
    Returns user's user agent form request.
    :param request: http request
    :type request: django.http.HttpRequest
    :return: user agent
    :rtype: instance
    """
    from user_agents import parse
    return parse(request.META.get('HTTP_USER_AGENT', ''))


def get_location_from_request(request):
    """
    Returns location object.
    :param request: http request
    :type request: django.http.HttpRequest
    :return: location instance or empty dict
    :rtype: instance or dict
    """
    from django.contrib.gis.geoip2 import GeoIP2
    from geoip2.errors import AddressNotFoundError

    user_ip = get_ip_from_request(request=request)
    g = GeoIP2()
    try:
        location = g.city(user_ip)
    except AddressNotFoundError:
        return dict()
    else:
        return location
