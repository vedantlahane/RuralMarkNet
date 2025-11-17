"""Integration tests for account views."""
from __future__ import annotations

from datetime import timedelta

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from accounts.models import EmailVerificationToken, User


class SignupViewTests(TestCase):
    """Verify that the signup flow works."""

    def test_signup_requires_email_verification(self) -> None:
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
        pending_url = reverse("accounts:verify-email-pending")
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.headers["Location"].startswith(pending_url))

        user = User.objects.get(username="customer1")
        self.assertFalse(user.is_active)
        self.assertFalse(user.email_verified)
        self.assertTrue(EmailVerificationToken.objects.filter(user=user).exists())


class EmailVerificationViewTests(TestCase):
    """Exercise the verification and resend endpoints."""

    def setUp(self) -> None:
        self.user = User.objects.create_user(
            username="pending-user",
            email="pending@example.com",
            password="safe-password-123",
            role=User.Roles.CUSTOMER,
            is_active=False,
            email_verified=False,
        )

    def test_successful_verification_activates_user(self) -> None:
        token = EmailVerificationToken.issue_for_user(self.user, expires_in=timedelta(minutes=10))
        response = self.client.get(reverse("accounts:verify-email", args=[token.token]))
        expected_redirect = reverse(self.user.get_dashboard_url())
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.headers["Location"], expected_redirect)

        refreshed = User.objects.get(pk=self.user.pk)
        self.assertTrue(refreshed.email_verified)
        self.assertTrue(refreshed.is_active)
        self.assertTrue(EmailVerificationToken.objects.filter(user=self.user, consumed_at__isnull=False).exists())

    def test_expired_token_redirects_back_to_pending(self) -> None:
        token = EmailVerificationToken.objects.create(
            user=self.user,
            expires_at=timezone.now() - timedelta(hours=1),
        )
        response = self.client.get(reverse("accounts:verify-email", args=[token.token]))
        self.assertEqual(response.status_code, 302)
        expected = f"{reverse('accounts:verify-email-pending')}?email={self.user.email}"
        self.assertEqual(response.headers["Location"], expected)

        refreshed = User.objects.get(pk=self.user.pk)
        self.assertFalse(refreshed.email_verified)

    def test_resend_creates_fresh_token(self) -> None:
        old_token = EmailVerificationToken.issue_for_user(self.user, expires_in=timedelta(minutes=5))
        response = self.client.post(
            reverse("accounts:verify-email-resend"),
            data={"email": self.user.email},
        )
        self.assertEqual(response.status_code, 302)
        pending_base = reverse("accounts:verify-email-pending")
        self.assertTrue(response.headers["Location"].startswith(pending_base))

        latest = EmailVerificationToken.objects.filter(user=self.user).first()
        self.assertIsNotNone(latest)
        if latest is None:  # pragma: no cover - typing guard
            self.fail("Expected to find a replacement token")
        self.assertNotEqual(latest.token, old_token.token)
