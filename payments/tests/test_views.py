"""Tests for payment initiation view."""
from __future__ import annotations

from decimal import Decimal
from unittest.mock import patch

from django.test import TestCase
from django.urls import reverse

from accounts.models import AuditLog, User
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
        self.farmer = User.objects.create_user(
            username="farmer",
            password="pass1234",
            role=User.Roles.FARMER,
        )
        self.product = Product.objects.create(
            name="Pumpkin",
            category=Product.Categories.VEGETABLES,
            price=Decimal("25.00"),
            inventory=5,
            farmer=self.farmer,
        )
        self.order = Order.objects.create(customer=self.customer, status=Order.Status.PENDING)
        self.order.items.create(product=self.product, quantity=1, price=Decimal("25.00"))  # type: ignore[attr-defined]

    def test_redirects_when_not_logged_in(self) -> None:
        response = self.client.get(reverse("payments:start", args=[self.order.pk]))
        self.assertEqual(response.status_code, 302)

    def test_customer_can_load_payment_page(self) -> None:
        self.client.login(username="customer", password="pass1234")
        response = self.client.get(reverse("payments:start", args=[self.order.pk]))
        self.assertEqual(response.status_code, 200)

    def test_farmer_preferences_filter_choices(self) -> None:
        self.client.login(username="customer", password="pass1234")

        # Default should include COD
        response = self.client.get(reverse("payments:start", args=[self.order.pk]))
        provider_codes = [code for code, _ in response.context["form"].fields["provider"].choices]
        self.assertIn(Payment.Providers.COD.value, provider_codes)

        # Farmer disallows COD
        self.farmer.accepted_payment_methods = [Payment.Providers.STRIPE.value]  # type: ignore[assignment]
        self.farmer.save(update_fields=["accepted_payment_methods"])

        response = self.client.get(reverse("payments:start", args=[self.order.pk]))
        provider_codes = [code for code, _ in response.context["form"].fields["provider"].choices]
        self.assertNotIn(Payment.Providers.COD.value, provider_codes)

    def test_cod_selection_updates_order_without_gateway(self) -> None:
        self.client.login(username="customer", password="pass1234")

        with patch("payments.views.dispatch_payment") as mock_dispatch:
            response = self.client.post(
                reverse("payments:start", args=[self.order.pk]),
                data={"provider": Payment.Providers.COD.value},
                follow=True,
            )

        self.assertFalse(mock_dispatch.called)
        self.assertRedirects(response, reverse("orders:detail", args=[self.order.pk]))

        self.order.refresh_from_db()
        self.assertEqual(self.order.payment_status, Order.PaymentStatus.UNPAID)
        self.assertEqual(self.order.status, Order.Status.CONFIRMED)
        payment = Payment.objects.get(order=self.order, provider=Payment.Providers.COD.value)
        self.assertEqual(payment.status, Payment.Status.INITIATED)
        self.assertTrue(
            AuditLog.objects.filter(action__icontains="Cash on delivery", object_id=str(self.order.pk)).exists()
        )

    def test_multiple_farmers_limit_payment_methods(self) -> None:
        self.client.login(username="customer", password="pass1234")

        second_farmer = User.objects.create_user(
            username="farmer_two",
            password="pass1234",
            role=User.Roles.FARMER,
        )
        second_farmer.accepted_payment_methods = [Payment.Providers.STRIPE.value]  # type: ignore[assignment]
        second_farmer.save(update_fields=["accepted_payment_methods"])

        second_product = Product.objects.create(
            name="Carrot",
            category=Product.Categories.VEGETABLES,
            price=Decimal("10.00"),
            inventory=10,
            farmer=second_farmer,
        )
        self.order.items.create(product=second_product, quantity=1, price=Decimal("10.00"))  # type: ignore[attr-defined]

        response = self.client.get(reverse("payments:start", args=[self.order.pk]))
        provider_codes = [code for code, _ in response.context["form"].fields["provider"].choices]
        self.assertEqual(provider_codes, [Payment.Providers.STRIPE.value, Payment.Providers.PAYPAL.value])
