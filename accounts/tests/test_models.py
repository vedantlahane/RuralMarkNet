"""Unit tests for the custom user model."""
from __future__ import annotations

from datetime import timedelta

from django.test import TestCase
from django.utils import timezone

from accounts.models import EmailVerificationToken, User


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

    def test_email_verification_token_lifecycle(self) -> None:
        user = User.objects.create_user(username="customer", password="safe-pass")
        token = EmailVerificationToken.issue_for_user(user, expires_in=timedelta(minutes=5))
        self.assertTrue(token.is_valid())

        token.expires_at = timezone.now() - timedelta(minutes=1)
        token.save(update_fields=["expires_at"])
        self.assertTrue(token.is_expired())
        self.assertFalse(token.is_valid())
