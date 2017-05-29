from django.conf import settings

def toolset_proc(request):
    return {
            'GOOGLE_MAPS_KEY': settings.GOOGLE_MAPS_KEY,
            'MAIN_SITE_REDIRECT': 'https://zeroelement.com',
            'HACKED_PRESS_LINK' : 'https://hacked.press'
            }
