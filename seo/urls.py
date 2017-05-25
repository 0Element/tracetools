#coding:utf-8
from django.conf.urls import url

from views import SeoDataView


urlpatterns = [url(r"^$", SeoDataView.as_view(), name="index"),]
