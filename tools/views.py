from __future__ import unicode_literals
from ua_parser import user_agent_parser

from django.conf import settings
from django.contrib import messages
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render, render_to_response
from django.template import RequestContext
from django.views import View
from django.views.generic import FormView, TemplateView

from utilities.mixins import FormInvalidRenderMixin, RateLimitMixin
from .forms import DomainForm, IPForm, HeadersForm, IPorDomainForm
from .utils import (parse_email_header, get_abuse_tool, get_mx_lookup_tool, get_dns_black_list_tool,
                    get_http_headers, get_dnssec_tool, get_ip_info, get_who_is, get_ns_tool, get_client_ip )


class HomePage(View):
    """
    Home page view
    """

    def get(self, request):
        template_name = 'home.html'
        ip = get_client_ip(self.request)
        info = get_ip_info(ip)
        ua = request.META.get('HTTP_USER_AGENT')
        parsed_string_ua = user_agent_parser.Parse(ua)

        return render(request, 'home.html', {"user_ip": ip , 'user_info': info, 'user_agent': parsed_string_ua})


class EmailHeadersView(FormInvalidRenderMixin, RateLimitMixin, FormView):
    """
    Parses email headers.
    """
    http_method_names = ('get', 'post')
    form_class = HeadersForm
    template_name = 'email_tools/email_headers.html'
    rate_limit = '100/d'

    def form_valid(self, form):
        is_valid, parsed_headers = parse_email_header(self.request.POST.get('headers'))
        if not is_valid:
            messages.add_message(self.request, messages.ERROR, 'Headers is invalid')
        context = self.get_context_data()
        context['result'] = parsed_headers
        return self.render_to_response(context)


class AbuseEmailView(FormInvalidRenderMixin, RateLimitMixin, FormView):
    """
    Fetches abuse emails for specified domain.
    """
    http_method_names = ('get', 'post')
    form_class = DomainForm
    template_name = 'email_tools/abuse_email_lookup.html'
    rate_limit = '100/d'

    def form_valid(self, form):
        abuse_info = get_abuse_tool(form.cleaned_data.get('domain'))
        context = self.get_context_data()
        if abuse_info:
            context['result'] = abuse_info
        else:
            context['not_info'] = 'We have no information for this domain in the database. ' \
                            'Lacking any better address, we suggest sending mail to ' \
                            'abuse at this domain and all super-domains of this domain. ' \
                            'Since we are not omniscient, we do not know about every domain ' \
                            'on the net. If you know the contact address for a domain that ' \
                            'is not in our database, please contact us '
        return self.render_to_response(context)


class MXLookupView(FormInvalidRenderMixin, RateLimitMixin, FormView):
    """
    Looking for mx entries for specified domain.
    """
    http_method_names = ('get', 'post')
    form_class = DomainForm
    template_name = 'email_tools/mx_look_up.html'
    rate_limit = '100/d'

    def form_valid(self, form):
        mx_info = get_mx_lookup_tool(form.cleaned_data.get('domain'))
        if not mx_info:
            messages.add_message(self.request, messages.ERROR, 'No MX entries were found for specified domain')
        context = self.get_context_data()
        context['result'] = mx_info
        return self.render_to_response(context)


class HTTPHeadersView(FormInvalidRenderMixin, RateLimitMixin, FormView):
    http_method_names = ('get', 'post')
    form_class = DomainForm
    template_name = 'ip_tools/http_headers.html'
    rate_limit = '100/d'

    def form_valid(self, form):
        headers = get_http_headers(form.cleaned_data.get('domain'))
        if not headers:
            messages.add_message(self.request, messages.ERROR, 'Nothing found for this domain')
        context = self.get_context_data()
        context['result'] = headers
        return self.render_to_response(context)


class DNSSecView(FormInvalidRenderMixin, RateLimitMixin, FormView):
    http_method_names = ('get', 'post')
    form_class = DomainForm
    template_name = 'ip_tools/dnssec_tool.html'
    rate_limit = '100/d'

    def form_valid(self, form):
        status, info = get_dnssec_tool(form.cleaned_data.get('domain'))
        if not info:
            messages.add_message(self.request, messages.ERROR, 'Nothing found for this domain')
        context = self.get_context_data()
        context['status'] = status
        context['result'] = info
        return self.render_to_response(context)


class IPLookupView(FormInvalidRenderMixin, RateLimitMixin, FormView):
    http_method_names = ('get', 'post')
    form_class = IPForm
    template_name = 'ip_tools/ip_lookup.html'
    rate_limit = '100/d'

    def form_valid(self, form):
        info = get_ip_info(form.cleaned_data.get('ip'))
        if not info:
            messages.add_message(self.request, messages.ERROR, 'Nothing found for this IP address')
        context = self.get_context_data()
        context['result'] = info
        return self.render_to_response(context)


class WhoIsView(FormInvalidRenderMixin, RateLimitMixin, FormView):
    http_method_names = ('get', 'post')
    form_class = IPorDomainForm
    template_name = 'ip_tools/who_is.html'
    rate_limit = '100/d'

    def form_valid(self, form):
        print(form.cleaned_data.get('ip_or_domain'))
        info = get_who_is(form.cleaned_data.get('ip_or_domain'))
        if not info:
            messages.add_message(self.request, messages.ERROR, 'Nothing found for specified domain')
        context = self.get_context_data()
        context['result'] = info
        return self.render_to_response(context)


class NSLookupView(FormInvalidRenderMixin, RateLimitMixin, FormView):
    http_method_names = ('get', 'post')
    form_class = DomainForm
    template_name = 'ip_tools/ns_lookup.html'
    rate_limit = '100/d'

    def form_valid(self, form):
        info = get_ns_tool(form.cleaned_data.get('domain'))
        if not info:
            messages.add_message(self.request, messages.ERROR, 'No NS found for specified domain')
        context = self.get_context_data()
        context['result'] = info
        return self.render_to_response(context)


def handler404(request):
    response = render_to_response('404.html', {}, RequestContext(request))
    response.status_code = 404
    return response


def handler500(request):
    response = render_to_response('500.html', {}, RequestContext(request))
    response.status_code = 500
    return response
