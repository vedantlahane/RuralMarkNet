"""URL patterns for orders and checkout."""
from __future__ import annotations

from django.urls import path

from .views import (
    AdminOrderListView,
    AdminOrderUpdateView,
    CartView,
    CheckoutView,
    OrderDetailView,
    OrderCancelView,
    OrderListView,
    add_to_cart,
)

app_name = "orders"

urlpatterns = [
    path("cart/", CartView.as_view(), name="cart"),
    path("cart/add/<int:product_id>/", add_to_cart, name="add-to-cart"),
    path("checkout/", CheckoutView.as_view(), name="checkout"),
    path("my/", OrderListView.as_view(), name="list"),
    path("my/<int:pk>/", OrderDetailView.as_view(), name="detail"),
    path("my/<int:pk>/cancel/", OrderCancelView.as_view(), name="cancel"),
    path("admin/orders/", AdminOrderListView.as_view(), name="admin-list"),
    path("admin/orders/<int:pk>/", AdminOrderUpdateView.as_view(), name="admin-update"),
]
