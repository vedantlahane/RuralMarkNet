"""Form validation tests for account workflows."""
from __future__ import annotations

from django.test import RequestFactory, TestCase

from accounts.forms import LoginForm, UserRegistrationForm
from accounts.models import User


class RegistrationFormTests(TestCase):
    """Ensure the registration form enforces business rules."""

    def test_registration_form_requires_language(self) -> None:
        form = UserRegistrationForm(
            data={
                "username": "newuser",
                "email": "user@example.com",
                "password1": "complex-pass-123",
                "password2": "complex-pass-123",
                "role": "customer",
                "preferred_language": "hi",
            }
        )
        self.assertTrue(form.is_valid())


class LoginFormTests(TestCase):
    """Ensure login form enforces verification requirements."""

    def setUp(self) -> None:
        self.factory = RequestFactory()
        self.user = User.objects.create_user(
            username="pending",
            email="pending@example.com",
            password="complex-pass-123",
            email_verified=False,
        )

    def test_unverified_user_cannot_login(self) -> None:
        form = LoginForm(
            request=self.factory.post("/accounts/login/"),
            data={
                "username": self.user.username,
                "password": "complex-pass-123",
            },
        )
        self.assertFalse(form.is_valid())
        self.assertIn("verify", str(form.errors["__all__"]).lower())
