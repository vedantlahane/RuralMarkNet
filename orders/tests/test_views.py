"""Tests for order creation views."""
from __future__ import annotations

from decimal import Decimal

from django.test import TestCase
from django.urls import reverse

from accounts.models import User
from orders.models import Order
from products.models import Product


class CartViewTests(TestCase):
    """Ensure cart operations behave."""

    def setUp(self) -> None:
        self.customer = User.objects.create_user(
            username="customer",
            password="pass1234",
            role=User.Roles.CUSTOMER,
        )
        farmer = User.objects.create_user(
            username="farmer",
            password="pass1234",
            role=User.Roles.FARMER,
        )
        self.product = Product.objects.create(
            name="Apple",
            category=Product.Categories.FRUITS,
            price=Decimal("5.00"),
            inventory=10,
            farmer=farmer,
        )

    def test_add_to_cart_requires_login(self) -> None:
        response = self.client.post(reverse("orders:add-to-cart", args=[self.product.pk]))
        self.assertEqual(response.status_code, 302)

    def test_customer_can_add_to_cart(self) -> None:
        self.client.login(username="customer", password="pass1234")
        self.client.post(reverse("orders:add-to-cart", args=[self.product.pk]))
        order = Order.objects.get(customer=self.customer)
        self.assertEqual(order.items.count(), 1)
