"""Unit tests for the custom user model."""
from __future__ import annotations

from django.test import TestCase

from accounts.models import User


class UserModelTests(TestCase):
    """Validate behaviour of the custom user model."""

    def test_user_role_helpers(self) -> None:
        user = User.objects.create_user(
            username="farmer1",
            password="safe-password",
            role=User.Roles.FARMER,
        )
        self.assertTrue(user.is_farmer)
        self.assertFalse(user.is_customer)
        self.assertIn("Farmer", str(user))
