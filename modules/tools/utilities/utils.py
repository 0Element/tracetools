import base64
import hashlib
import httplib
import json
import re
import socket
import time
import urllib2
import zlib
from ssl import CertificateError

from django.conf import settings
from django.core.cache import caches

from . import get_ip_from_request
from .validators import is_valid_domain_name

_PERIODS = {
    's': 1,
    'm': 60,
    'h': 60 * 60,
    'd': 24 * 60 * 60,
}

# regex for parse rate limit that looks like this '1000/d'
rate_re = re.compile('([\d]+)/([\d]*)([smhd])?')


def user_or_ip(request):
    """
    Returns current user's pk as a string or IP address in case of the user in not authenticated.
    :param request: Http request
    :return: pk or IP address
    :rtype: str
    """
    return str(request.user.pk) if request.user.is_authenticated() else get_ip_from_request(request)


def _split_rate(rate):
    """
    Splits passed rate.
    Rate looks like '1000/d' that means 1000 requests per day.
    Possible time options: s - per second, m - per minute, h - per hour, d - per day.
    :param rate: rate limit
    :rtype: str or tuple
    :return: count of requests and seconds
    :rtype: tuple
    """
    if isinstance(rate, tuple):
        return rate
    count, multi, period = rate_re.match(rate).groups()
    count = int(count)
    if not period:
        period = 's'
    seconds = _PERIODS[period.lower()]
    if multi:
        seconds *= int(multi)
    return count, seconds


def _get_window(value, period):
    """
    I don't know wtf is this but it works.
    So it's better to not touch this until we realize wtf is going on here.
    :param value: user pk as a string or IP address
    :type value: str
    :param period: time in seconds
    :type period: int
    :return: something
    """
    ts = int(time.time())
    if period == 1:
        return ts
    if not isinstance(value, bytes):
        value = value.encode('utf-8')
    w = ts - (ts % period) + (zlib.crc32(value) % period)
    if w < ts:
        return w + period
    return w


def _make_cache_key(rate, value):
    """
    Saves rate to the cache with value as ID.
    :param rate: rate limit
    :type rate: str or tuple
    :param value: user pk as a string or IP address
    :type value: str
    :return: unique string
    :rtype: str
    """
    count, period = _split_rate(rate)
    safe_rate = '%d/%ds' % (count, period)
    window = _get_window(value, period)
    parts = [safe_rate, value, str(window)]
    return 'rl:' + hashlib.md5(u''.join(parts).encode('utf-8')).hexdigest()


def is_rate_limited(request, rate=None, increment=False):
    """
    Checks if rate limited for current user.
    :param request: Http request
    :param rate: rate limit
    :type rate: str or tuple
    :param increment: increment count of requests
    :type increment: bool
    :return: True of False
    :rtype: bool
    """
    old_limited = getattr(request, 'limited', False)

    if rate is None:
        request.limited = old_limited
        return False

    usage = get_usage_count(request, rate, increment)

    limited = usage.get('count') > usage.get('limit')
    if increment:
        request.limited = old_limited or limited
    return limited


def get_usage_count(request, rate=None, increment=False):
    """
    Returns count of available requests, current limit and time left for this limit.
    :param request: Http request
    :param rate: rate limit
    :param increment: increment count of requests
    :return: described data
    :rtype: dict
    """
    limit, period = _split_rate(rate)
    cache = caches['default']
    value = user_or_ip(request)

    cache_key = _make_cache_key(rate, value)
    time_left = _get_window(value, period) - int(time.time())
    initial_value = 1 if increment else 0
    added = cache.add(cache_key, initial_value)
    if added:
        count = initial_value
    else:
        if increment:
            try:
                count = cache.incr(cache_key)
            except ValueError:
                count = initial_value
        else:
            count = cache.get(cache_key, initial_value)
    return {'count': count, 'limit': limit, 'time_left': time_left}


def is_local_address(url):
    local_hosts = settings.LOCAL_HOSTS
    try:
        url = socket.gethostbyname(url)
    except socket.error:
        return False
    else:
        if url in local_hosts:
            return True
        else:
            return False


def pluralize(value, arg='s'):
    """
    Returns a plural suffix if the value is not 1. By default, 's' is used as
    the suffix:
    * If value is 0, vote{{ value|pluralize }} displays "0 votes".
    * If value is 1, vote{{ value|pluralize }} displays "1 vote".
    * If value is 2, vote{{ value|pluralize }} displays "2 votes".
    If an argument is provided, that string is used instead:
    * If value is 0, class{{ value|pluralize:"es" }} displays "0 classes".
    * If value is 1, class{{ value|pluralize:"es" }} displays "1 class".
    * If value is 2, class{{ value|pluralize:"es" }} displays "2 classes".
    If the provided argument contains a comma, the text before the comma is
    used for the singular case and the text after the comma is used for the
    plural case:
    * If value is 0, cand{{ value|pluralize:"y,ies" }} displays "0 candies".
    * If value is 1, cand{{ value|pluralize:"y,ies" }} displays "1 candy".
    * If value is 2, cand{{ value|pluralize:"y,ies" }} displays "2 candies".
    """
    if ',' not in arg:
        arg = ',' + arg
    bits = arg.split(',')
    if len(bits) > 2:
        return ''
    singular_suffix, plural_suffix = bits[:2]

    try:
        if float(value) != 1:
            return plural_suffix
    except ValueError:  # Invalid string that's not a number.
        pass
    except TypeError:  # Value isn't a string or a number; maybe it's a list?
        try:
            if len(value) != 1:
                return plural_suffix
        except TypeError:  # len() of unsized object.
            pass
    return singular_suffix


def get_service_servers(service_id):
    """
    Get service id
    Return list choices with servers number and countries
    """
    # TODO: added multicontrolles
    servers = [(0, u'Default')]
    for address in settings.CONTROLLERS_SERVER:
        try:
            conn = httplib.HTTPConnection(address)
            conn.request("GET", "/services/{}/".format(service_id))
            response = conn.getresponse()
        except Exception, e:
            pass # if has not connection with controller
        else:
            if response.status == 200:
                encoded_data = response.read()
                try:
                    decoded_data = json.loads(base64.b64decode(encoded_data))
                    for index, value in decoded_data.items():
                        servers.append((index, value))
                except ValueError:
                    pass # if cant parse response from controller
    return servers


def timeit(method):
    """
    Decorator for measuring function execution.
    :param method: function of method
    :return: decorated function
    """

    def timed(*args, **kw):
        ts = time.time()
        result = method(*args, **kw)
        te = time.time()

        print '%r (%r, %r) %2.2f sec' % \
              (method.__name__, args, kw, te-ts)
        return result

    return timed


def get_host_ip(host):
    """
    Returns host ip or None
    :param host: domain name
    :type host: str
    :return: ip or None
    :rtype: str or None
    """
    try:
        ip = socket.gethostbyname(host.replace('http://', '').replace('https://', ''))
    except socket.gaierror:
        ip = None
    return ip


def supports_https(domain):
    """
    Return True if website with passed domain name supports https.
    :param domain: domain name
    :type domain: str
    :return: True or False
    :rtype: bool
    """
    if is_valid_domain_name(domain):
        try:
            urllib2.urlopen('https://' + domain)
        except (IOError, CertificateError):
            return False
        else:
            return True
    else:
        return False
