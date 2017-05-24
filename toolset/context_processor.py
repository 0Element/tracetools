from .settingslocal import GOOGLE_MAPS_KEY

def toolset_proc(request):
    return {
            'GOOGLE_MAPS_KEY': GOOGLE_MAPS_KEY,
            'MAIN_SITE_REDIRECT': 'https://zeroelement.com'
            }
