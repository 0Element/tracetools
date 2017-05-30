"""toolset URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.10/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
from __future__ import unicode_literals

from django.conf import settings
from django.conf.urls.static import static
from django.conf.urls import include, url
from django.contrib import admin
from modules.tools.views import ( HomePage, EmailHeadersView, AbuseEmailView, MXLookupView,
HTTPHeadersView,DNSSecView, IPLookupView, WhoIsView, NSLookupView, handler404, handler500 )

urlpatterns = [
    url(r'^admin/', admin.site.urls),
    url(r'^$', HomePage.as_view(), name='home'),
    url(r'^email-headers/$', EmailHeadersView.as_view(), name='email-headers'),
    url(r'^email-abuse-info/$', AbuseEmailView.as_view(), name='email-abuse-info'),
    url(r'^mx-lookup/$', MXLookupView.as_view(), name='mx-lookup'),

    url(r'^http-headers/$', HTTPHeadersView.as_view(), name='http-headers'),
    url(r'^dns-sec/$', DNSSecView.as_view(), name='dns-sec'),
    url(r'^ip-lookup/$', IPLookupView.as_view(), name='ip-lookup'),
    url(r'^who-is/$', WhoIsView.as_view(), name='who-is'),
    url(r'^ns-lookup/$', NSLookupView.as_view(), name='ns-lookup'),
    url(r'^seo/', include('modules.seo.urls', namespace='seo')),

]
