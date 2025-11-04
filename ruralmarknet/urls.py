"""RuralMarkNet URL configuration."""
from __future__ import annotations

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

from products.views import LanguageSwitchView

urlpatterns = [
    path("i18n/setlang/", LanguageSwitchView.as_view(), name="set_language"),
    path("i18n/", include("django.conf.urls.i18n")),
]

i18n_urlpatterns = [
    path("admin/", admin.site.urls),
    # Public-facing catalogue and checkout
    path("", include("products.urls")),
    path("accounts/", include("accounts.urls")),
    path("orders/", include("orders.urls")),
    path("deliveries/", include("deliveries.urls")),
    path("payments/", include("payments.urls")),
    # Role-based portals (our application dashboards)
    path("portal/admin/", include(("ruralmarknet.portal_admin_urls", "portal-admin"))),
    path("portal/farmer/", include(("ruralmarknet.portal_farmer_urls", "portal-farmer"))),
    path("portal/customer/", include(("ruralmarknet.portal_customer_urls", "portal-customer"))),
]

urlpatterns += i18n_urlpatterns

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
