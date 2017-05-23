from __future__ import unicode_literals

import json
import re

import mandrill
import pika
from django.conf import settings
from django.utils.html import strip_tags

from .helpers import send_queue_message


def send_email(subject, html_content, recipients, from_email=None):
    """
    """
    if from_email is None:
        from_email = settings.DEFAULT_FROM_EMAIL

    if settings.DEBUG or settings.TESTING_MODE:
        message = json.dumps({
            "headers": {'Reply-To': from_email},
            'subject': subject,
            # 'body': strip_tags(re.findall(r'<body .+>.+</body>', html_content, re.DOTALL)[0]),
            'body': html_content,
            "to": [email for email in recipients],
            "from_email": from_email
        })

        connection = pika.BlockingConnection(pika.ConnectionParameters(**settings.RABBITMQ_CONFIG["connect"]))
        channel = connection.channel()
        channel.queue_declare(queue='send_email_queue', durable=True)
        channel.basic_publish(exchange='',
                              routing_key='send_email_queue',
                              body=message,
                              properties=pika.BasicProperties(
                                  delivery_mode=2,
                              ))

    else:
        convert_recipients = [{'email': email, 'type': 'to'} for email in recipients]
        message = json.dumps({
            'from_email': from_email,
            'from_name': 'Zero Element',
            'headers': {'Reply-To': from_email},
            'html': html_content,
            'important': True,
            'inline_css': True,
            'metadata': {'website': 'zerolement.io'},
            'subject': subject,
            'text': strip_tags(re.findall(r'<body .+>.+</body>', html_content, re.DOTALL)[0]),
            'to': convert_recipients,
        })
        try:
            connection = pika.BlockingConnection(pika.ConnectionParameters(**settings.RABBITMQ_CONFIG["connect"]))
            channel = connection.channel()
            channel.queue_declare(queue='send_email_queue', durable=True)
            channel.basic_publish(exchange='',
                                  routing_key='send_email_queue',
                                  body=message,
                                  properties=pika.BasicProperties(
                                      delivery_mode=2,
                                  ))
            print " [x] Sent %r" % (message,)
            connection.close()

        except mandrill.Error as error:
            print(error)


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
