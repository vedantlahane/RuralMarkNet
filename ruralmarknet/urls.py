"""RuralMarkNet URL configuration."""
from __future__ import annotations

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from django.utils.translation import gettext_lazy as _

urlpatterns = [
    path("i18n/", include("django.conf.urls.i18n")),
]

i18n_urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("products.urls")),
    path("accounts/", include("accounts.urls")),
    path("orders/", include("orders.urls")),
    path("deliveries/", include("deliveries.urls")),
    path("payments/", include("payments.urls")),
]

urlpatterns += i18n_urlpatterns

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
