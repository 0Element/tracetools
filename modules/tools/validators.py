from __future__ import unicode_literals

import re

pattern = re.compile(
    r'^(([a-zA-Z]{1})|([a-zA-Z]{1}[a-zA-Z]{1})|'
    r'([a-zA-Z]{1}[0-9]{1})|([0-9]{1}[a-zA-Z]{1})|'
    r'([a-zA-Z0-9][-_.a-zA-Z0-9]{0,61}[a-zA-Z0-9]))\.'
    r'([a-zA-Z]{2,13}|[a-zA-Z0-9-]{2,30}.[a-zA-Z]{2,3})$'
)


def validate_domain(domain):
    """
    Validates domain name.

    Example:

        >>> validate_domain('example.com')
        True

        >>> validate_domain('example.com/')
        False

    :param domain: domain name to validate
    :type domain: str
    """
    return pattern.match(domain)
