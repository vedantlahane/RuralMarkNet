"""Portal routes for customers (namespace: portal-customer).

This lightweight namespace mainly exposes a role-specific dashboard and
room for future customer-only endpoints.
"""
from __future__ import annotations

from django.urls import path

from accounts.views import DashboardCustomerView
from deliveries.views import CustomerDeliveryDetailView, CustomerDeliveryListView

app_name = "portal-customer"

urlpatterns = [
    path("", DashboardCustomerView.as_view(), name="dashboard"),
    path(
        "deliveries/",
        CustomerDeliveryListView.as_view(detail_url_name="portal-customer:deliveries-detail"),
        name="deliveries-list",
    ),
    path("deliveries/<int:pk>/", CustomerDeliveryDetailView.as_view(), name="deliveries-detail"),
]
