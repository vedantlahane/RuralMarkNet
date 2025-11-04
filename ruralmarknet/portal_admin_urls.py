"""Portal routes serving administrator-only views (namespace: portal-admin)."""
from __future__ import annotations

from django.urls import path

from orders.views import AdminOrderListView, AdminOrderUpdateView
from products.views import AdminProductListView, AdminProductUpdateView, ProductModerationView
from deliveries.views import AdminDeliveryListView, AdminDeliveryDetailView
from accounts.views import AdminAuditLogListView, AdminFinancialReportView, DashboardAdminView

app_name = "portal-admin"

urlpatterns = [
    path("", DashboardAdminView.as_view(), name="dashboard"),
    path("orders/", AdminOrderListView.as_view(), name="orders-list"),
    path("orders/<int:pk>/", AdminOrderUpdateView.as_view(), name="orders-update"),
    path("products/", AdminProductListView.as_view(), name="products-list"),
    path("products/<slug:slug>/moderate/", ProductModerationView.as_view(), name="products-moderate"),
    path("products/<slug:slug>/edit/", AdminProductUpdateView.as_view(), name="products-update"),
    path("deliveries/", AdminDeliveryListView.as_view(), name="deliveries-list"),
    path("deliveries/<int:pk>/", AdminDeliveryDetailView.as_view(), name="deliveries-detail"),
    path("audit/", AdminAuditLogListView.as_view(), name="audit-list"),
    path("reports/financial/", AdminFinancialReportView.as_view(), name="reports-financial"),
]
