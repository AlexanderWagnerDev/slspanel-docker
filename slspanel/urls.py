from django.contrib import admin
from django.urls import path, include
from django.conf.urls.i18n import i18n_patterns
from django.views.generic import RedirectView
import os

urlpatterns = [
    path('', RedirectView.as_view(url=f'/{os.getenv("LANG", "en")}/', permanent=False)),
]

urlpatterns += i18n_patterns(
    path('admin/', admin.site.urls),
    path('', include('streams.urls')),
)