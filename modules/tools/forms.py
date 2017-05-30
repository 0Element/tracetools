from __future__ import unicode_literals

from django import forms
from django.core.validators import validate_ipv46_address

from .validators import validate_domain


class HeadersForm(forms.Form):
    headers = forms.CharField(widget=forms.Textarea())


class DomainForm(forms.Form):
    domain = forms.URLField(help_text='protocol name required (http/https/etc)')


class IPForm(forms.Form):
    ip = forms.GenericIPAddressField(help_text='IPv4 or IPv6 address')


class IPorDomainForm(forms.Form):
    ip_or_domain = forms.CharField(help_text='Domain, IPv4 or IPv6 address')

    def clean_ip_or_domain(self):
        ip_or_domain = self.cleaned_data.get('ip_or_domain')
        try:
            validate_ipv46_address(ip_or_domain)
        except forms.ValidationError:
            ipv46 = False
        else:
            ipv46 = True
        try:
            if not validate_domain(ip_or_domain):
                raise forms.ValidationError('Invalid domain name')
        except forms.ValidationError:
            domain = False
        else:
            domain = True
        if not any([ipv46, domain]):
            raise forms.ValidationError('Invalid domain name or IP4/IP6')
        return ip_or_domain
