"""URL patterns for product catalogue."""
from __future__ import annotations

from django.urls import path

from .views import ProductDetailView, ProductListView

app_name = "products"

urlpatterns = [
    path("", ProductListView.as_view(), name="home"),
    path("products/", ProductListView.as_view(), name="list"),
    path("products/<slug:slug>/", ProductDetailView.as_view(), name="detail"),
]
