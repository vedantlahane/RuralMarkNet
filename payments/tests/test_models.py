"""Tests for payment model transitions."""
from __future__ import annotations

from decimal import Decimal

from django.test import TestCase

from accounts.models import User
from orders.models import Order
from products.models import Product
from payments.models import Payment


class PaymentModelTests(TestCase):
    """Ensure order status updates when payment succeeds."""

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
            name="Banana",
            category=Product.Categories.FRUITS,
            price=Decimal("15.00"),
            inventory=10,
            farmer=farmer,
        )
        self.order = Order.objects.create(customer=self.customer, status=Order.Status.PENDING)
        self.order.items.create(product=product, quantity=2, price=Decimal("15.00"))

    def test_mark_successful_updates_order(self) -> None:
        payment = Payment.objects.create(
            order=self.order,
            provider=Payment.Providers.STRIPE,
            amount=self.order.total_amount,
        )
        payment.mark_successful("txn_123", {"id": "evt_1"})
        self.order.refresh_from_db()
        self.assertEqual(self.order.payment_status, Order.PaymentStatus.PAID)
