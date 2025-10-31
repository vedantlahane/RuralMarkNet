"""View tests for product listing."""
from __future__ import annotations

from django.test import TestCase
from django.urls import reverse

from accounts.models import User
from products.models import Product


class ProductListViewTests(TestCase):
    """Basic smoke tests for product listing."""

    def setUp(self) -> None:
        farmer = User.objects.create_user(
            username="farmer",
            password="test-pass",
            role=User.Roles.FARMER,
        )
        Product.objects.create(
            name="Fresh Milk",
            category=Product.Categories.DAIRY,
            price=40,
            inventory=5,
            farmer=farmer,
        )

    def test_list_view_returns_products(self) -> None:
        response = self.client.get(reverse("products:list"))
        self.assertContains(response, "Fresh Milk")
