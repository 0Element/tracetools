#coding:utf-8
from django.http.response import JsonResponse, Http404
from django.views.generic import View

from .forms import SeoDataForm
from .models import SeoData


class SeoDataView(View):
    """
    Save page seo data
    """
    def get(self, request):
        """
        """
        if not request.user.is_staff or not request.GET.get("url"):
            raise Http404()

        try:
            seo = SeoData.objects.get(url=request.GET["url"])
        except SeoData.DoesNotExist:
            seo = SeoData()

        return JsonResponse({"status": True, "data": 
            {"meta_description": seo.meta_description, "page_h1": seo.page_h1, 
             "title_tag": seo.title_tag}})

    def post(self, request):
        """
        Save form data from url
        """
        if not request.user.is_staff or not request.POST.get("url"):
            raise Http404()

        print request.POST
        try:
            seo_instance = SeoData.objects.get(url=request.POST["url"])
        except SeoData.DoesNotExist:
            seo_instance = SeoData()
        
        form = SeoDataForm(request.POST, instance=seo_instance)
        if not form.is_valid():
            return JsonResponse({"status": False, "errors": form.errors})

        form.save()
        return JsonResponse({"status": True})

