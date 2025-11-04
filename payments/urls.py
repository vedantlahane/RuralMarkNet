"""Payments URL configuration."""
from __future__ import annotations

from django.urls import path

from .views import PaymentInitView, PaymentResultView, StripeWebhookView

app_name = "payments"

urlpatterns = [
    path("start/<int:order_id>/", PaymentInitView.as_view(), name="start"),
    path("result/<int:order_id>/", PaymentResultView.as_view(), name="result"),
    path("webhooks/stripe/", StripeWebhookView.as_view(), name="stripe-webhook"),
]
