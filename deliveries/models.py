"""Delivery scheduling models."""
from __future__ import annotations

from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _

from orders.models import Order


class Delivery(models.Model):
    """Represents delivery logistics tied to an order."""

    class Status(models.TextChoices):
        PENDING = "pending", _("Pending confirmation")
        SCHEDULED = "scheduled", _("Scheduled")
        IN_TRANSIT = "in_transit", _("In transit")
        COMPLETED = "completed", _("Completed")
        CANCELLED = "cancelled", _("Cancelled")

    order = models.OneToOneField(Order, on_delete=models.CASCADE, related_name="delivery")
    driver_name = models.CharField(max_length=120, blank=True)
    contact_number = models.CharField(max_length=20, blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    assigned_farmer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="deliveries",
    )
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-updated_at"]

    def __str__(self) -> str:
        return f"Delivery for order #{self.order_id}"
