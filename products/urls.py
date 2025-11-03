"""URL patterns for product catalogue."""
from __future__ import annotations

from django.urls import path

from .views import (
    AdminProductListView,
    AdminProductUpdateView,
    FarmerProductListView,
    ProductCreateView,
    ProductDetailView,
    ProductListView,
    ProductUpdateView,
)

app_name = "products"

urlpatterns = [
    path("", ProductListView.as_view(), name="home"),
    path("products/", ProductListView.as_view(), name="list"),
    path("products/manage/", FarmerProductListView.as_view(), name="manage"),
    path("products/new/", ProductCreateView.as_view(), name="create"),
    path("products/<slug:slug>/", ProductDetailView.as_view(), name="detail"),
    path("products/<slug:slug>/edit/", ProductUpdateView.as_view(), name="update"),
    path("admin/products/", AdminProductListView.as_view(), name="admin-manage"),
    path("admin/products/<slug:slug>/edit/", AdminProductUpdateView.as_view(), name="admin-update"),
]
