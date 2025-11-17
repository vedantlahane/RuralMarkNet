"""Service helpers for account workflows."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta
from typing import Optional

from django.conf import settings
from django.contrib.sites.shortcuts import get_current_site
from django.core.mail import send_mail
from django.http import HttpRequest
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from .models import EmailVerificationToken, User


@dataclass(slots=True)
class VerificationPayload:
    """Return object describing the latest verification attempt."""

    token: EmailVerificationToken
    verification_url: str


class EmailVerificationService:
    """High-level helper for issuing verification emails."""

    EXPIRATION_HOURS = 48

    @classmethod
    def issue_token(cls, user: User) -> EmailVerificationToken:
        """Create or replace an email verification token for a user."""

        expires_in = timedelta(hours=cls.EXPIRATION_HOURS)
        return EmailVerificationToken.issue_for_user(user, expires_in=expires_in)

    @classmethod
    def build_verification_url(
        cls, request: HttpRequest | None, token: EmailVerificationToken
    ) -> str:
        """Return an absolute URL to the verification endpoint."""

        path = reverse("accounts:verify-email", args=[token.token])
        if request is not None:
            return request.build_absolute_uri(path)
        site = get_current_site(request)
        scheme = "https" if not settings.DEBUG else "http"
        return f"{scheme}://{site.domain}{path}"

    @classmethod
    def send_verification(
        cls, user: User, request: HttpRequest | None
    ) -> Optional[VerificationPayload]:
        """Send a verification email when possible and return payload."""

        token = cls.issue_token(user)
        if not user.email:
            return None
        verification_url = cls.build_verification_url(request, token)
        context = {
            "user": user,
            "verification_url": verification_url,
            "hours_valid": cls.EXPIRATION_HOURS,
            "is_debug": settings.DEBUG,
        }
        message = render_to_string("accounts/emails/verification_email.txt", context)
        send_mail(
            subject=_("Confirm your RuralMarkNet email"),
            message=message,
            from_email=getattr(
                settings,
                "DEFAULT_FROM_EMAIL",
                "RuralMarkNet <noreply@ruralmarknet.local>",
            ),
            recipient_list=[user.email],
        )
        return VerificationPayload(token=token, verification_url=verification_url)

