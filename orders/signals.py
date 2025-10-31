"""Order related signals."""
from __future__ import annotations

from django.db.models.signals import post_save
from django.dispatch import receiver

from deliveries.models import Delivery

from .models import Order


@receiver(post_save, sender=Order)
def ensure_delivery_exists(sender, instance: Order, created: bool, **_: object) -> None:
    """Create a delivery record when an order is placed."""
    if instance.status in {Order.Status.PENDING, Order.Status.CONFIRMED}:
        Delivery.objects.get_or_create(order=instance, defaults={"assigned_farmer": instance.items.first().product.farmer if instance.items.exists() else None})
