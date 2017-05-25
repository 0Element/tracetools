#coding:utf-8
from __future__ import unicode_literals
import re
# from django.http import HttpResponseRedirect
# from ..views import logout_view

# Set up a rendered TemplateResponse
# from django.template.response import TemplateResponse
from .models import SeoData


# array(
#     '/<h1>(.*)<\/h1>/i',
#     '/<title>(.*)<\/title>/i',
#     '/<meta name="description" content="(.*)"\/>/i'
#     ),


H1_REGEX = re.compile(r"<h1([^>]*)>(.*?)</h1>", re.I | re.U)
TITLE_REGEX = re.compile(r"<title>(.*?)</title>", re.I | re.U)
DESCRIPTION_REGEX = re.compile(r"""<meta name="description" content="(.*)"/>""", re.I | re.U)

#     '/<meta name="description" content="(.*)"\/>/i'
# a.sub("<h1>ffd</h1>", "<h1>fggsaaaaa</h1>dsadsa</h1>")
class SeoMiddleware(object):
    """
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):

        response = self.get_response(request)

        try:
            seo = SeoData.objects.get(url=request.path)
        except SeoData.DoesNotExist:
            pass
        else:
            res = unicode(response.content.decode("utf-8"))
            if seo.page_h1:
                res = H1_REGEX.sub(ur"<h1\1>%s</h1>" % seo.page_h1, res)
            if seo.title_tag:
                res = TITLE_REGEX.sub(ur"<title>%s</title>" % seo.title_tag, res)
            if seo.meta_description:
                res = DESCRIPTION_REGEX.sub(ur"""<meta name="description" content="%s"/>""" % seo.meta_description, res)
            response.content = res

        return response
