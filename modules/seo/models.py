#coding:utf-8
from django.db import models
from django.utils.translation import ugettext_lazy as _


class SeoData(models.Model):
    """
    """
    url = models.CharField(_("Page url"), max_length=255)
    title_tag = models.CharField(_("Title tag"), max_length=255, blank=True)
    meta_description = models.CharField(_("Meta description"), max_length=255, blank=True)
    page_h1 = models.CharField(_("Page h1"), max_length=255, blank=True)

    class Meta:
        pass
