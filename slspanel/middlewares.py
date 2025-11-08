from django.utils import translation
import os

class ForceEnvLanguageMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        self.lang_code = os.getenv("LANG", "en")

    def __call__(self, request):
        translation.activate(self.lang_code)
        request.LANGUAGE_CODE = self.lang_code
        response = self.get_response(request)
        translation.deactivate()
        return response