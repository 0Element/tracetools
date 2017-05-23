from __future__ import unicode_literals

import hashlib
from datetime import datetime

from django.conf import settings
from django.contrib import messages

from .exceptions import RateLimited
from .utils import is_rate_limited


class RateLimitMixin(object):
    """
    Restricts access to a view according to specified rate limit.
    Possible time options: s - per second, m - per minute, h - per hour, d - per day.
    Example:
        class View(RateLimitMixin):
            rate_limit = '5/m'
    """
    rate_limit = '5/m'

    def dispatch(self, request, *args, **kwargs):
        if is_rate_limited(request, self.rate_limit, True):
            raise RateLimited()
        else:
            return super(RateLimitMixin, self).dispatch(request, *args, **kwargs)


class FormInvalidRenderMixin(object):
    def form_invalid(self, form):
        """
        If the form is invalid, re-render the context data with the
        data-filled form and errors.
        """
        messages.add_message(self.request, messages.ERROR, form.non_field_errors().as_text())
        return self.render_to_response(self.get_context_data())
