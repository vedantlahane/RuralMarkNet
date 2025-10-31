"""Tests for payment initiation view."""
from __future__ import annotations

from decimal import Decimal

from django.test import TestCase
from django.urls import reverse

from accounts.models import User
from orders.models import Order
from products.models import Product
from payments.models import Payment


class PaymentInitViewTests(TestCase):
    """Ensure the payment start endpoint requires authentication."""

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
        product = Product.objects.create(
            name="Pumpkin",
            category=Product.Categories.VEGETABLES,
            price=Decimal("25.00"),
            inventory=5,
            farmer=farmer,
        )
        self.order = Order.objects.create(customer=self.customer, status=Order.Status.PENDING)
        self.order.items.create(product=product, quantity=1, price=Decimal("25.00"))

    def test_redirects_when_not_logged_in(self) -> None:
        response = self.client.get(reverse("payments:start", args=[self.order.pk]))
        self.assertEqual(response.status_code, 302)

    def test_customer_can_load_payment_page(self) -> None:
        self.client.login(username="customer", password="pass1234")
        response = self.client.get(reverse("payments:start", args=[self.order.pk]))
        self.assertEqual(response.status_code, 200)
