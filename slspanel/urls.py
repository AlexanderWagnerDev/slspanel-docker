from django.conf import settings
from django.contrib import admin
from django.shortcuts import redirect
from django.urls import path, include
from django.conf.urls.i18n import i18n_patterns
from django.views.decorators.http import require_GET


@require_GET
def root_redirect(request):
    return redirect(f"/{settings.LANGUAGE_CODE}/")


urlpatterns = [
    path('', root_redirect),
]

urlpatterns += i18n_patterns(
    path('admin/', admin.site.urls),
    path('', include('streams.urls')),
)