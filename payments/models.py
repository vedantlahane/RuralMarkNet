"""Payment tracking models."""
from __future__ import annotations

from django.db import models
from django.utils.translation import gettext_lazy as _

from orders.models import Order


class Payment(models.Model):
    """Records a payment attempt for an order."""

    class Providers(models.TextChoices):
        STRIPE = "stripe", _("Stripe")
        PAYPAL = "paypal", _("PayPal")
        COD = "cod", _("Cash on delivery")

    class Status(models.TextChoices):
        INITIATED = "initiated", _("Initiated")
        SUCCESS = "success", _("Success")
        FAILED = "failed", _("Failed")
        REFUNDED = "refunded", _("Refunded")

    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="payments")
    provider = models.CharField(max_length=20, choices=Providers.choices)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.INITIATED)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3, default="INR")
    transaction_id = models.CharField(max_length=120, blank=True)
    raw_response = models.JSONField(blank=True, default=dict)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["provider", "transaction_id"])]

    def __str__(self) -> str:
        order_reference = getattr(self, "order_id", None)
        if order_reference is None:
            order_reference = getattr(self.order, "pk", "?")
        return f"Payment {self.pk} for order #{order_reference}"

    def mark_successful(self, transaction_id: str, payload: dict[str, object]) -> None:
        """Mark the payment as successful and update related order."""
        self.transaction_id = transaction_id
        self.status = self.Status.SUCCESS
        self.raw_response = payload
        self.save(update_fields=["transaction_id", "status", "raw_response", "updated_at"])
        self.order.payment_status = self.order.PaymentStatus.PAID
        self.order.save(update_fields=["payment_status"])
