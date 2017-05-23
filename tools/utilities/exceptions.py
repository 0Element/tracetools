from __future__ import unicode_literals

from django.core.exceptions import PermissionDenied


class RateLimited(PermissionDenied):
    pass
