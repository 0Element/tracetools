#coding:utf-8
from django import forms

from .models import SeoData


class SeoDataForm(forms.ModelForm):
    class Meta:
        model = SeoData
        exclude = ()
        # fields = ("url", "title_tag", "meta_description", "page_h1")
