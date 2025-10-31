"""URL configuration for deliveries."""
from __future__ import annotations

from django.urls import path

from .views import DeliveryDetailView, DeliveryListView, DeliveryUpdateView

app_name = "deliveries"

urlpatterns = [
    path("", DeliveryListView.as_view(), name="list"),
    path("<int:pk>/", DeliveryDetailView.as_view(), name="detail"),
    path("<int:pk>/edit/", DeliveryUpdateView.as_view(), name="update"),
]
