"""Tests for delivery views."""
from __future__ import annotations

from django.test import TestCase
from django.urls import reverse

from accounts.models import User
from deliveries.models import Delivery
from orders.models import Order, OrderItem
from products.models import Product


class DeliveryViewTests(TestCase):
    """Ensure authentication checks for delivery views."""

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
            name="Lettuce",
            category=Product.Categories.VEGETABLES,
            price=20,
            inventory=5,
            farmer=self.farmer,
        )
        order = Order.objects.create(customer=self.customer, status=Order.Status.PENDING)
        OrderItem.objects.create(order=order, product=product, quantity=1, price=20)
        self.delivery, _ = Delivery.objects.get_or_create(order=order)
        self.delivery.assigned_farmer = self.farmer
        self.delivery.save(update_fields=["assigned_farmer"])

    def test_delivery_list_requires_login(self) -> None:
        response = self.client.get(reverse("deliveries:list"))
        self.assertEqual(response.status_code, 302)

    def test_customer_can_view_delivery(self) -> None:
        self.client.login(username="customer", password="pass1234")
        response = self.client.get(reverse("deliveries:detail", args=[self.delivery.pk]))
        self.assertEqual(response.status_code, 200)
