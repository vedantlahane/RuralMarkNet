"""Integration tests for account views."""
from __future__ import annotations

from django.test import TestCase
from django.urls import reverse

from accounts.models import User


class SignupViewTests(TestCase):
    """Verify that the signup flow works."""

    def test_signup_creates_user(self) -> None:
        response = self.client.post(
            reverse("accounts:signup"),
            data={
                "username": "customer1",
                "email": "customer@example.com",
                "password1": "strong-secret-42",
                "password2": "strong-secret-42",
                "role": User.Roles.CUSTOMER,
                "preferred_language": "en",
            },
        )
        self.assertEqual(response.status_code, 302)
        self.assertTrue(User.objects.filter(username="customer1").exists())
