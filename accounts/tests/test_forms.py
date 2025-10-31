"""Form validation tests for account workflows."""
from __future__ import annotations

from django.test import TestCase

from accounts.forms import UserRegistrationForm


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
