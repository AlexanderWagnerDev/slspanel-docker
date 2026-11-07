from django.conf import settings
from django.utils import translation


class ForceEnvLanguageMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        self.lang_code = settings.LANGUAGE_CODE

    def __call__(self, request):
        translation.activate(self.lang_code)
        request.LANGUAGE_CODE = self.lang_code
        try:
            return self.get_response(request)
        finally:
            translation.deactivate()
