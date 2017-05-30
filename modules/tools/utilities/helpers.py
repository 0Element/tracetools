# coding: utf-8
"""
Some small and useful functions
"""
import base64
import datetime
import hashlib
import json
import re
import time
import urllib
import urllib2
from io import FileIO, BufferedWriter
from os.path import join, abspath, dirname
from uuid import uuid4

import pika
from django.conf import settings
from django.template.defaultfilters import pluralize


def to_int(value, default=None):
    """
    Try cast value to integer
    @param value:
    @param default: default value if not int
    @return:
    """
    try:
        value = int(value)
    except (TypeError, ValueError):
        return default
    else:
        return value


def rel(*x):
    """Easy way to set setting paths"""
    return join(abspath(dirname(__file__)), *x)


def current_timestamp():
    """
    Get current timestamp
    @return: int
    """
    return int(time.time())


def to_timestamp(value):
    """
    Convert datetime to timestamp
    @param value: datetime
    @return: int
    """
    if not isinstance(value, datetime.date):
        return None

    return time.mktime(value.timetuple())


def remove_html_tags(data):
    """
    Remove html tags from string
    """
    p = re.compile(r'<.*?>')
    return p.sub('', data)


def decimal_ceil(x):
    """
    math.ceil analog which works
    """
    int_x = int(x)
    if x - int_x == 0:
        return int_x
    return int_x + 1


def to_utf8(string):
    """
    Convert to utf8
    """
    return unicode(str(string), 'utf-8').encode('utf-8')


def objects_to_choices(queryset):
    """
    Get choices list from model queryset
    """
    res = []
    for elm in queryset:
        res.append((elm.pk, unicode(elm)))
    return res


def value_from_list(key, values, by_first=False):
    """
    Get 0-index from collection of double tuples/lists by first key value
    print value_from_list(((1, "key1",), (2, "key2",), (3, "key3",),), "key2")
    will output:`2`
    """
    i, j = (1, 0,) if not by_first else (0, 1,)
    for elm in values:
        if elm[i] == key:
            return elm[j]
    return None


def get_key_by_value(needvalue, mydict):
    """
    Get key of dictionary value
    """
    return [key for key, value in mydict.iteritems() if value == needvalue][0]


def get_md5(text):
    """
    MD5 function short name
    """
    return hashlib.md5(text).hexdigest()


def generate_filename(extension, with_path=True, base_folder=None):
    """
    Generate unique filename with folder path
    """
    name = get_md5(str(uuid4()))
    # if not extension:
    # extension = get_file_extension()
    if base_folder is not None:
        base_folder = "%s/" % base_folder.rstrip("/")
    else:
        base_folder = ""

    if with_path:
        return "%s%s/%s/%s/%s.%s" % (base_folder, name[0], name[1], name[2], name, extension)
    else:
        return "%s%s.%s" % (base_folder, name, extension)


def get_file_extension(filename):
    """
    Get extension of file
    """
    if not filename:
        return ""

    dotpos = filename.rfind(".")
    return filename[dotpos + 1:].lower() if dotpos != -1 else ""


def make_upload_path(folder):
    """
    Generates upload path for FileField
    """

    def _uploader(instance, filename):
        return generate_filename(get_file_extension(filename), base_folder=folder)

    return _uploader


def save_uploaded_from_request(uploaded, extension, raw_data):
    """
    raw_data: if True, upfile is a HttpRequest object with raw post data
    as the file, rather than a Django UploadedFile from request.FILES 
    """
    filename = "/tmp/%s.%s" % (uuid4(), extension)
    try:
        with BufferedWriter(FileIO(filename, "wb")) as dest:
            # if the "advanced" upload, read directly from the HTTP request 
            # with the Django 1.3 functionality
            if raw_data:
                foo = uploaded.read(1024)
                while foo:
                    dest.write(foo)
                    foo = uploaded.read(1024)
                    # if not raw, it was a form upload so read in the normal Django chunks fashion
            else:
                for c in uploaded.chunks():
                    dest.write(c)
            return filename
    except IOError:
        # could not open the file most likely
        return False
    except Exception, e:
        return str(e)


def url_encode(value, key=None):
    """
    Simple encode function
    """
    return base64.b64encode(value)
    # enc = []
    # for i in range(len(clear)):
    #     key_c = key[i % len(key)]
    #     enc_c = chr((ord(clear[i]) + ord(key_c)) % 256)
    #     enc.append(enc_c)
    # return base64.urlsafe_b64encode("".join(enc))


def url_decode(value, key=None):
    """
    Simple decode function
    """
    return base64.b64decode(value)
    # dec = []
    # enc = base64.urlsafe_b64decode(enc)
    # for i in range(len(enc)):
    #     key_c = key[i % len(key)]
    #     dec_c = chr((256 + ord(enc[i]) - ord(key_c)) % 256)
    #     dec.append(dec_c)
    # return "".join(dec)


def send_queue_message(connection, queue_name, message):
    channel = connection.channel()
    channel.queue_declare(queue=queue_name, durable=True)
    channel.basic_publish(exchange="", routing_key=queue_name, body=message,
                          properties=pika.BasicProperties(delivery_mode=2))
    return True


def send_controller_message(data):
    try:
        connection = pika.BlockingConnection(
            pika.ConnectionParameters(**settings.RABBITMQ_CONFIG["connect"])
        )
    except pika.exceptions.ConnectionClosed:
        from services.models import Task
        message = json.dumps(data)
        task = Task(data=message)
        task.save()
    else:
        message = json.dumps(data)
        send_queue_message(
            connection,
            settings.RABBITMQ_CONFIG[settings.CONTROLLER_QUEUE],
            message
        )


def recaptcha_validation(forms, request):
    from django.conf import settings
    url = "https://www.google.com/recaptcha/api/siteverify"
    if request is not None:
        values = {
            'secret': settings.GOOGLE_RECAPTCHA_SECRET_KEY,
            'response': request.POST.get(u'g-recaptcha-response', None),
            'remoteip': request.META.get("REMOTE_ADDR", None),
        }
        data = urllib.urlencode(values)
        req = urllib2.Request(url, data)
        response = urllib2.urlopen(req)
        result = json.loads(response.read())
    else:
        raise forms.ValidationError(u'Only humans are allowed to submit this form.')

    # result["success"] will be True on a success
    if not result["success"]:
        raise forms.ValidationError(u'Only humans are allowed to submit this form.')

    return True


def date_now_plus_year():
    """
    Return +1 year date
    """
    return (datetime.date.today() + datetime.timedelta(days=365))


def human_date(delta):
    """
    Function that return humanize date
    """
    if delta < datetime.timedelta(minutes=1):
        unit = "{0} {1}".format(delta.seconds, pluralize(delta.seconds, "second,seconds"))
    elif delta < datetime.timedelta(hours=1):
        unit = "{0} {1}".format(delta.seconds//60, pluralize(delta.seconds//60, "minute,minutes"))
    elif delta < datetime.timedelta(days=1):
        unit = "{0} {1}".format(delta.seconds//3600, pluralize(delta.seconds//3600, "hour,hours"))
    elif delta < datetime.timedelta(weeks=1):
        unit = "{0} {1}".format(delta.days, pluralize(delta.days, "day,days"))
    elif delta <= datetime.timedelta(days=30):
        unit = "{0} {1}".format(delta.days//7, pluralize(delta.days//7, "week,weeks"))
    elif delta <= datetime.timedelta(days=365):
        unit = "{0} {1}".format(delta.days//30, pluralize(delta.days//30, "month,months"))
    else:
        unit = "{0} {1}".format(delta.days//365, pluralize(delta.days//365, "year,years"))
    return unit
