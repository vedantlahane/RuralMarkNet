"""URL configuration for deliveries."""
from __future__ import annotations

from django.urls import path

from .views import (
    CustomerDeliveryListView,
    CustomerDeliveryDetailView,
    FarmerDeliveryUpdateView,
)

app_name = "deliveries"

urlpatterns = [
    path("", CustomerDeliveryListView.as_view(), name="list"),
    path("<int:pk>/", CustomerDeliveryDetailView.as_view(), name="detail"),
    path("<int:pk>/edit/", FarmerDeliveryUpdateView.as_view(), name="update"),
]
