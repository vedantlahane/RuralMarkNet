"""Integration tests for the checkout flow."""
from __future__ import annotations

from datetime import date, timedelta

from django.test import TestCase
from django.urls import reverse

from accounts.models import User
from orders.models import Order
from payments.models import Payment
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
        order.items.create(product=self.product, quantity=2, price=50)  # type: ignore[attr-defined]
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
                "payment_provider": Payment.Providers.COD.value,
            },
        )
        self.assertRedirects(response, reverse("orders:detail", args=[order.pk]))
        order.refresh_from_db()
        self.assertEqual(order.status, Order.Status.CONFIRMED)
        self.assertEqual(order.payment_status, Order.PaymentStatus.UNPAID)
        self.assertEqual(order.delivery_address, "123 Market Street")
        payment = Payment.objects.get(order=order)
        self.assertEqual(payment.provider, Payment.Providers.COD.value)
        self.assertEqual(payment.status, Payment.Status.INITIATED)
