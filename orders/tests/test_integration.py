"""Integration tests for the checkout flow."""
from __future__ import annotations

from datetime import date, timedelta

from django.test import TestCase
from django.urls import reverse

from accounts.models import User
from orders.models import Order
from products.models import Product


class CheckoutFlowTests(TestCase):
    """Simulate a customer submitting the checkout form."""

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
        self.product = Product.objects.create(
            name="Spinach",
            category=Product.Categories.VEGETABLES,
            price=50,
            inventory=10,
            farmer=self.farmer,
        )

    def test_checkout_places_order(self) -> None:
        order = Order.objects.create(customer=self.customer)
        order.items.create(product=self.product, quantity=2, price=50)
        session = self.client.session
        session["cart_id"] = order.pk
        session.save()

        self.client.login(username="customer", password="pass1234")
        response = self.client.post(
            reverse("orders:checkout"),
            data={
                "delivery_address": "123 Market Street",
                "scheduled_date": date.today() + timedelta(days=1),
                "scheduled_window": "morning",
                "notes": "Leave at the doorstep",
            },
        )
        self.assertEqual(response.status_code, 302)
        order.refresh_from_db()
        self.assertEqual(order.status, Order.Status.PENDING)
        self.assertTrue(hasattr(order, "delivery"))
        self.assertEqual(order.delivery_address, "123 Market Street")
