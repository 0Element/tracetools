from __future__ import unicode_literals

import httplib
import os
import re
import socket
from email.errors import HeaderParseError
from email.parser import HeaderParser
from urlparse import urlparse

import dns
import geoip2
from django.conf import settings
from django.contrib.gis.geoip2 import GeoIP2
from geoip2.errors import AddressNotFoundError
from ipwhois import IPWhois
from ipwhois.utils import get_countries

def get_domain_name(domain):
    """
    Returns domain name by parsing passed string by means of urlparse.
    :param domain: string with domain name
    :type domain: str
    :return: domain name
    :rtype: str
    """
    return urlparse(domain).netloc or urlparse(domain).path


def parse_email_header(header):
    """
    Parses email headers and returns it as ordered list.
    :param header: headers
    :type header: str
    :return: parsed headers
    :rtype: tuple
    """
    headers_order = {
        'date': 1,
        'from': 2,
        'to': 3,
        'subject': 4,
        'return-path': 5,
        'delivered-to': 6,
        'in-reply-to': 7,
        'message-id': 8,
        'mime-version': 9,
        'received': 10,
        'x-mailer': 11
    }
    try:
        parser = HeaderParser()
        header = header.encode('utf-8')
        parsed_headers = parser.parsestr(header)
        if parsed_headers:
            return True, [{'key': header[0], 'value': header[1], 'order': headers_order.get(header[0].lower()) or 100}
                          for header in parsed_headers.items()]
        else:
            return False, {}
    except (HeaderParseError, Exception):
        return False, {}


def get_abuse_tool(domain):
    """
    Returns abuse email list for specified domain.
    :param domain: domain name
    :type domain: str
    :return: list of emails
    :rtype: list
    """
    domain = get_domain_name(domain)
    try:
        ip = socket.gethostbyname(domain)
        obj = IPWhois(ip)
        res = obj.lookup_whois()
        emails = res['nets'][0]['emails'] or res['nets'][1]['emails']
    except (AddressNotFoundError, Exception):
        return False
    else:
        try:
            return emails if type(emails) in (list, type) else emails.split('\n')
        except AttributeError:
            return ['Not found abuse contact info']


def get_mx_lookup_tool(domain):
    """
    Returns MX entries for specified domain name.
    :param domain: domain name
    :type domain: str
    :return: list with MX entries
    :rtype: list
    """
    domain = get_domain_name(domain)
    try:
        mx_look_up = [
            {
                'server': x.exchange,
                'priority': x.preference,
                'ip': socket.gethostbyname(domain)
            } for x in dns.resolver.query(domain, 'MX')
        ]
    except (dns.resolver.NXDOMAIN, Exception):
        return None
    else:
        return mx_look_up


def get_dns_black_list_tool(ip):
    """
    Returns list of DNS servers with a mark if specified IP address listed there.
    :param ip: IP address
    :type ip: str
    :return: list with DNS servers
    :rtype: list
    """
    black_lists = [
        'b.barracudacentral.org', 'bl.spamcannibal.org', 'bl.spamcop.net', 'blacklist.woody.ch', 'cbl.abuseat.org',
        'cdl.anti-spam.org.cn', 'combined.abuse.ch', 'combined.rbl.msrbl.net', 'db.wpbl.info',
        'dnsbl-1.uceprotect.net', 'dnsbl-2.uceprotect.net', 'dnsbl-3.uceprotect.net', 'dnsbl.cyberlogic.net',
        'dnsbl.sorbs.net', 'drone.abuse.ch', 'drone.abuse.ch', 'duinv.aupads.org', 'dul.dnsbl.sorbs.net', 'dul.ru',
        'dyna.spamrats.com', 'dynip.rothen.com', 'http.dnsbl.sorbs.net', 'images.rbl.msrbl.net',
        'ips.backscatterer.org', 'ix.dnsbl.manitu.net', 'korea.services.net', 'misc.dnsbl.sorbs.net',
        'noptr.spamrats.com', 'ohps.dnsbl.net.au', 'omrs.dnsbl.net.au', 'orvedb.aupads.org', 'osps.dnsbl.net.au',
        'osrs.dnsbl.net.au', 'owfs.dnsbl.net.au', 'pbl.spamhaus.org', 'phishing.rbl.msrbl.net', 'probes.dnsbl.net.au',
        'proxy.bl.gweep.ca', 'rbl.interserver.net', 'rdts.dnsbl.net.au', 'relays.bl.gweep.ca', 'relays.nether.net',
        'residential.block.transip.nl', 'ricn.dnsbl.net.au', 'rmst.dnsbl.net.au', 'smtp.dnsbl.sorbs.net',
        'socks.dnsbl.sorbs.net', 'spam.abuse.ch', 'spam.dnsbl.sorbs.net', 'spam.rbl.msrbl.net', 'spam.spamrats.com',
        'spamrbl.imp.ch', 't3direct.dnsbl.net.au', 'tor.dnsbl.sectoor.de', 'torserver.tor.dnsbl.sectoor.de',
        'ubl.lashback.com', 'ubl.unsubscore.com', 'virus.rbl.jp', 'virus.rbl.msrbl.net', 'web.dnsbl.sorbs.net',
        'wormrbl.imp.ch', 'xbl.spamhaus.org', 'zen.spamhaus.org', 'zombie.dnsbl.sorbs.net', 'virbl.dnsbl.bit.nl',
        'dnsbl.inps.de'
    ]

    black_list_look_up = []
    for black_list in black_lists:

        try:
            resolver = dns.resolver.Resolver()
            queue = '.'.join(reversed(str(ip).split('.'))) + '.' + black_list
            resolver.query(queue, 'A')
            resolver.query(queue, 'TXT')
        except (dns.resolver.NoAnswer, dns.resolver.NoNameservers):
            black_list_look_up.append({'ip': ip, 'address': black_list, 'is_present': None})
        except dns.resolver.NXDOMAIN:
            black_list_look_up.append({'ip': ip, 'address': black_list, 'is_present': False})
        except Exception:
            return None
        else:
            black_list_look_up.append({'ip': ip, 'address': black_list, 'is_present': True})
    return black_list_look_up


def get_http_headers(domain):
    """
    Returns HTTP headers for specified domain.
    :param domain: domain name
    :type domain: str
    :return: HTTP headers
    :rtype: dict
    """
    try:
        domain = get_domain_name(domain)
        conn = httplib.HTTPConnection(domain, timeout=5)
        conn.request('HEAD', '/index.html')
        res = conn.getresponse()
        headers = dict(res.getheaders())
    except Exception:
        return None
    else:
        return headers


def get_dnssec_tool(domain):
    """
    Returns something.
    :param domain: domain name
    :type domain: str
    :return: dns info
    :rtype: str
    """
    domain = get_domain_name(domain)
    dns_sec_fail = "dns.dnssec.ValidationFailure"
    dns_sec_no_name_serv = "IN NS: Server 127.0.0.1 UDP port 53 answered SERVFAIL"
    handl_fail = 'HANDLE QUERY FAILED (SERVER ERROR OR NO DNSKEY RECORD)'
    fail = 'No DNSKEY records found'
    try:
        response = dns.resolver.query(domain, dns.rdatatype.NS)
        nsname = response.rrset[0]
        response = dns.resolver.query(str(nsname), dns.rdatatype.A)
        nsaddr = response.rrset[0].to_text()
        request = dns.message.make_query(domain,
                                         dns.rdatatype.DNSKEY,
                                         want_dnssec=True)
        response = dns.query.udp(request, nsaddr)
        if response.rcode() != 0:
            return False, handl_fail
        answer = response.answer

        if len(answer) != 2:
            return False, fail

        name = dns.name.from_text(domain)
        try:
            dns.dnssec.validate(answer[0], answer[1], {name: answer[0]})
        except dns.dnssec.ValidationFailure:
            return False, dns_sec_fail
        else:
            dns_sec_good = str(response.answer[0])
            w = re.search('(\w*.\w*.\s\d*\s\w*\s\w*\s\d*\s\d\s\d)(\s)(.*)', dns_sec_good)
            return True, w.group(1)
    except (dns.resolver.NoNameservers, Exception):
        return False, dns_sec_no_name_serv


def get_ip_info(ip):
    """
    Returns some basic information about specified IP address.
    :param ip: IP address
    :type ip: str
    :return: basic information
    :rtype: dict
    """

    try:
        reader = GeoIP2()
        location = reader.city(ip)
        whois = IPWhois(ip).lookup()

        data = {
            'country': location['country_name'],  # Country
            'city': location['city'],  # City
            'region': location['region'],  # Region
            'lat': location['latitude'],  # Latitude
            'long': location['longitude'],  # Longitude    #
            'provider': whois['nets'][0]['name'],  # Provider
            'provider_info': whois['nets'][0]['address']  # Provider Info
        }
    except Exception:
        return None
    else:
        return data

def get_who_is(hostname):
    """
    Returns some information about hostname.
    :param hostname: domain name or IP address
    :type hostname: str
    :return: information about hostname
    :rtype: dict
    """

    try:
        domain = get_domain_name(hostname)
        info = IPWhois(socket.gethostbyname(domain)).lookup_rdap()
        data = {
            'country_code': info.get('asn_country_code'),  # Country code
            'date': info.get('asn_date'),  # Date
            'asncidr': info.get('asn_cidr'),  # Abstract Syntax Notation of Classless Inter-Domain Routing
            'asnr': info.get('asn_registry'),  # Abstract Syntax Notation Registartion
            'ip': info.get('query'),  # Ip
            'asn': info.get('asn'),  # Abstract Syntax Notation
            'updated': info.get('network').get('events')[0].get('timestamp') if info.get('network') and info.get('network').get('events') and info.get('network').get('events')[0].get('timestamp') else None,  # Updated
            'handle': info.get('network').get('handle') if info.get('network') else None,  # Handle
            'description': info.get('network').get('notices')[0].get('description') if info.get('network') and info.get('network').get('notices') and info.get('network').get('notices')[0].get('description') else None,  # Description
            'postal_code': info.get('network').get('postal_code') if info.get('network') else None,  # Postal
            'address': info.get('network').get('address') if info.get('network') else None,  # Address
            'city': info.get('network').get('city') if info.get('network') else None,  # City
            'name': info.get('network').get('name') if info.get('network') else None,  # Name
            'created': info.get('network').get('created') if info.get('network') else None,  # Created
            'country': info.get('network').get('country') if info.get('network') else None,  # Country
            'state': info.get('network').get('state') if info.get('network') else None,  # State
            'ip_range': info.get('network').get('range') if info.get('network') else None,  # Range of Ip
            'cidr': info.get('network').get('cidr') if info.get('network') else None  # Classless Inter-Domain Routing
        }
    except Exception as error:
        return None
    else:
        return data

def get_ns_tool(domain):
    """
    Returns domain NS entries.
    :param domain: domain name
    :type domain: str
    :return: NS entries
    :rtype: list
    """
    try:
        domain = get_domain_name(domain)
        data_nx = [server.to_text() for server in dns.resolver.query(domain, 'NS')]
    except Exception:
        return None
    else:
        return data_nx
