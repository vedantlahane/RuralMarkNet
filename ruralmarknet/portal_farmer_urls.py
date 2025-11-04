"""Portal routes for farmer workspace (namespace: portal-farmer)."""
from __future__ import annotations

from django.urls import path

from accounts.views import DashboardFarmerView
from products.views import (
    FarmerProductListView,
    ProductCreateView,
    ProductUpdateView,
    FarmerInventoryLowListView,
    FarmerInventoryBulkUpdateView,
)
from deliveries.views import (
    FarmerDeliveryListView,
    FarmerDeliveryDetailView,
    FarmerDeliveryUpdateView,
)

app_name = "portal-farmer"

urlpatterns = [
    path("", DashboardFarmerView.as_view(), name="dashboard"),
    path("products/", FarmerProductListView.as_view(), name="products-list"),
    path("products/new/", ProductCreateView.as_view(), name="products-create"),
    path("products/<slug:slug>/edit/", ProductUpdateView.as_view(), name="products-update"),
    path("inventory/low/", FarmerInventoryLowListView.as_view(), name="inventory-low"),
    path("inventory/update/", FarmerInventoryBulkUpdateView.as_view(), name="inventory-update"),
    path("deliveries/", FarmerDeliveryListView.as_view(), name="deliveries-list"),
    path("deliveries/<int:pk>/", FarmerDeliveryDetailView.as_view(), name="deliveries-detail"),
    path("deliveries/<int:pk>/update/", FarmerDeliveryUpdateView.as_view(), name="deliveries-update"),
]
