"""Order and cart related models."""
from __future__ import annotations

from decimal import Decimal

from django.conf import settings
from django.db import models, transaction
from django.utils.translation import gettext_lazy as _

from products.models import Product


class Order(models.Model):
    """Represents a customer order lifecycle."""

    class Status(models.TextChoices):
        CART = "cart", _("Cart")
        PENDING = "pending", _("Pending")
        CONFIRMED = "confirmed", _("Confirmed")
        SHIPPED = "shipped", _("Shipped")
        DELIVERED = "delivered", _("Delivered")
        CANCELLED = "cancelled", _("Cancelled")

    class PaymentStatus(models.TextChoices):
        UNPAID = "unpaid", _("Unpaid")
        PAID = "paid", _("Paid")
        REFUNDED = "refunded", _("Refunded")
        FAILED = "failed", _("Failed")

    customer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="orders",
    )
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.CART
    )
    payment_status = models.CharField(
        max_length=20, choices=PaymentStatus.choices, default=PaymentStatus.UNPAID
    )
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    delivery_address = models.TextField(blank=True)
    scheduled_date = models.DateField(null=True, blank=True)
    scheduled_window = models.CharField(max_length=50, blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"Order #{self.pk}"

    @transaction.atomic
    def recalculate_total(self) -> None:
        """Update the total amount based on order items."""
        total = self.items.aggregate(total=models.Sum("line_total"))
        self.total_amount = total["total"] or Decimal("0.00")
        self.save(update_fields=["total_amount"])

    @property
    def is_cart(self) -> bool:
        return self.status == self.Status.CART


class OrderItem(models.Model):
    """Line item for an order."""

    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name="items",
    )
    product = models.ForeignKey(Product, on_delete=models.PROTECT)
    quantity = models.PositiveIntegerField(default=1)
    price = models.DecimalField(max_digits=8, decimal_places=2)
    line_total = models.DecimalField(max_digits=10, decimal_places=2, editable=False)

    class Meta:
        unique_together = ("order", "product")

    def save(self, *args, **kwargs):
        self.line_total = Decimal(self.quantity) * self.price
        update_fields = kwargs.get("update_fields")
        if update_fields is not None and "line_total" not in update_fields:
            kwargs["update_fields"] = list(update_fields) + ["line_total"]
        super().save(*args, **kwargs)
        self.order.recalculate_total()

    def delete(self, *args, **kwargs):
        order = self.order
        super().delete(*args, **kwargs)
        order.recalculate_total()

    def __str__(self) -> str:
        return f"{self.product.name} x {self.quantity}"
