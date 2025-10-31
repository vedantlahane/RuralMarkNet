"""Tests for delivery models."""
from __future__ import annotations

from django.test import TestCase

from accounts.models import User
from deliveries.models import Delivery
from orders.models import Order
from products.models import Product


class DeliveryModelTests(TestCase):
    """Simple smoke tests for deliveries."""

    def setUp(self) -> None:
        self.customer = User.objects.create_user(
            username="customer",
            password="pass1234",
            role=User.Roles.CUSTOMER,
        )
        self.farmer = User.objects.create_user(
            username="farmer",
            password="pass1234",
            role=User.Roles.FARMER,
        )
        product = Product.objects.create(
            name="Potato",
            category=Product.Categories.VEGETABLES,
            price=30,
            inventory=10,
            farmer=self.farmer,
        )
        order = Order.objects.create(customer=self.customer, status=Order.Status.PENDING)
        order.items.create(product=product, quantity=1, price=30)
        self.delivery = Delivery.objects.create(order=order, assigned_farmer=self.farmer)

    def test_string_representation(self) -> None:
        self.assertIn(str(self.delivery.order.pk), str(self.delivery))
