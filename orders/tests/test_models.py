"""Model tests for order calculations."""
from __future__ import annotations

from decimal import Decimal

from django.test import TestCase

from accounts.models import User
from orders.models import Order, OrderItem
from products.models import Product


class OrderTotalsTests(TestCase):
    """Verify that totals recalculate with order items."""

    def setUp(self) -> None:
        self.customer = User.objects.create_user(
            username="customer",
            password="test-pass",
            role=User.Roles.CUSTOMER,
        )
        self.farmer = User.objects.create_user(
            username="farmer",
            password="test-pass",
            role=User.Roles.FARMER,
        )
        self.product = Product.objects.create(
            name="Carrot",
            category=Product.Categories.VEGETABLES,
            price=Decimal("10.00"),
            inventory=20,
            farmer=self.farmer,
        )

    def test_total_updates(self) -> None:
        order = Order.objects.create(customer=self.customer)
        OrderItem.objects.create(order=order, product=self.product, quantity=2, price=Decimal("10.00"))
        order.refresh_from_db()
        self.assertEqual(order.total_amount, Decimal("20.00"))
