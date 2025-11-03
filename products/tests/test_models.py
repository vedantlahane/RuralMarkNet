"""Tests for product models."""
from __future__ import annotations

from decimal import Decimal

from django.test import TestCase

from accounts.models import User
from products.models import Product


class ProductModelTests(TestCase):
    """Ensure string output and slug generation work."""

    def setUp(self) -> None:
        self.farmer = User.objects.create_user(
            username="farmer",
            password="test-pass",
            role=User.Roles.FARMER,
        )

    def test_slug_is_created(self) -> None:
        product = Product.objects.create(
            name="Organic Tomato",
            category=Product.Categories.VEGETABLES,
            price=50,
            inventory=10,
            farmer=self.farmer,
        )
        self.assertTrue(product.slug)
        self.assertIn("organic-tomato", product.slug)
        self.assertEqual(product.unit, Product.Units.KILOGRAM)
        self.assertEqual(product.unit_quantity, Decimal("1.00"))
        self.assertEqual(product.quality_grade, Product.QualityGrades.STANDARD)
        self.assertEqual(product.farming_practice, Product.FarmingPractices.CONVENTIONAL)
