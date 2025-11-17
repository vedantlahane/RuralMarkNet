"""Models for user accounts."""
from __future__ import annotations

import secrets
from datetime import timedelta
from typing import TYPE_CHECKING, cast

from django.apps import apps
from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

if TYPE_CHECKING:  # pragma: no cover - hints for type checkers only
    from payments.models import Payment as PaymentModel


class User(AbstractUser):
    """Custom user model with farmer/customer roles."""

    class Roles(models.TextChoices):
        FARMER = "farmer", _("Farmer")
        CUSTOMER = "customer", _("Customer")
        ADMIN = "admin", _("Administrator")

    PREFERRED_LANGUAGE_CHOICES = (
        ("en", _("English")),
        ("hi", _("Hindi")),
        ("mr", _("Marathi")),
    )

    role = models.CharField(
        max_length=20,
        choices=Roles.choices,
        default=Roles.CUSTOMER,
        help_text=_("Determines the level of access within the platform."),
    )
    phone_number = models.CharField(
        max_length=20,
        blank=True,
        help_text=_("Optional contact number for delivery coordination."),
    )
    preferred_language = models.CharField(
        max_length=8,
        choices=PREFERRED_LANGUAGE_CHOICES,
        default="en",
        help_text=_("Preferred language for the interface."),
    )
    address = models.TextField(blank=True)
    accepted_payment_methods = models.JSONField(
        default=None,
        blank=True,
        null=True,
        help_text=_("Payment method codes this farmer chooses to accept."),
    )
    email_verified = models.BooleanField(
        default=False,
        help_text=_("Indicates whether the user has confirmed their email address."),
    )

    @property
    def is_farmer(self) -> bool:
        """Return ``True`` when the user is a farmer."""
        return self.role == self.Roles.FARMER

    @property
    def is_customer(self) -> bool:
        """Return ``True`` when the user is a customer."""
        return self.role == self.Roles.CUSTOMER

    def __str__(self) -> str:
        display_role = self.get_role_display()  # type: ignore[attr-defined]
        name = self.get_full_name() or self.username
        return f"{name} ({display_role})"

    def get_dashboard_url(self) -> str:
        """Return the named URL for the user dashboard."""
        if getattr(self, "is_staff", False) or self.role == self.Roles.ADMIN:
            return "portal-admin:dashboard"
        if self.is_farmer:
            return "portal-farmer:dashboard"
        return "portal-customer:dashboard"

    def get_accepted_payment_methods(self) -> list[str]:
        """Return the allowed payment provider codes for this user."""

        payment_model = apps.get_model("payments", "Payment")
        if payment_model is None:
            return []
        payment_model = cast("type[PaymentModel]", payment_model)
        valid_methods = {code for code, _ in payment_model.Providers.choices}
        if not valid_methods:
            return []

        configured = self.accepted_payment_methods
        if isinstance(configured, list) and configured:
            configured_list = cast(list[str], configured)
            return [code for code in configured_list if code in valid_methods]
        return list(valid_methods)

    def supports_payment_method(self, method: str) -> bool:
        """Return True when the given provider code is permitted."""

        return method in self.get_accepted_payment_methods()


def _generate_verification_token() -> str:
    """Return a short-lived, URL-safe token for email verification."""

    # 32 bytes of entropy produces a 43 character URL-safe string.
    return secrets.token_urlsafe(32)


class EmailVerificationToken(models.Model):
    """One-time token that ensures an email address is owned by the user."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="verification_tokens",
    )
    token = models.CharField(max_length=64, unique=True, default=_generate_verification_token)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    consumed_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:  # pragma: no cover - repr helper
        return f"Email verification for {self.user}"  # type: ignore[str-format]

    @property
    def is_consumed(self) -> bool:
        """Return ``True`` when the token has already been used."""

        return self.consumed_at is not None

    def is_expired(self, at: timezone.datetime | None = None) -> bool:
        """Return True when the token is past its expiry."""

        at = at or timezone.now()
        return at >= self.expires_at

    def is_valid(self) -> bool:
        """Return True when the token can still be redeemed."""

        return not self.is_consumed and not self.is_expired()

    def mark_consumed(self) -> None:
        """Flag the token as redeemed."""

        if self.is_consumed:
            return
        self.consumed_at = timezone.now()
        self.save(update_fields=["consumed_at"])

    @classmethod
    def issue_for_user(cls, user: User, expires_in: timedelta | None = None) -> "EmailVerificationToken":
        """Create a replacement token for the user."""

        expires_in = expires_in or timedelta(hours=48)
        cls.objects.filter(user=user, consumed_at__isnull=True).delete()
        return cls.objects.create(user=user, expires_at=timezone.now() + expires_in)


class AuditLog(models.Model):
    """Immutable audit trail stored for administrator review."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="audit_logs",
    )
    action = models.CharField(max_length=150)
    app_label = models.CharField(max_length=100)
    model_name = models.CharField(max_length=100)
    object_id = models.CharField(max_length=64, blank=True)
    object_repr = models.CharField(max_length=255, blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = _("Audit log entry")
        verbose_name_plural = _("Audit log entries")

    def __str__(self) -> str:
        actor = getattr(self.user, "get_full_name", lambda: None)()
        actor_display = actor or getattr(self.user, "username", "system") if self.user else "system"
        return f"{self.action} by {actor_display}"

    @classmethod
    def record(
        cls,
        *,
        user: User | None,
        action: str,
        instance: models.Model | None = None,
        metadata: dict[str, object] | None = None,
    ) -> "AuditLog":
        """Helper for creating a log entry with minimal boilerplate."""

        if instance is not None:
            object_id = str(getattr(instance, "pk", ""))
            object_repr = str(instance)
            app_label = instance._meta.app_label
            model_name = instance._meta.model_name
        else:
            object_id = ""
            object_repr = ""
            app_label = "system"
            model_name = "event"

        return cls.objects.create(
            user=user,
            action=action,
            app_label=app_label,
            model_name=model_name,
            object_id=object_id,
            object_repr=object_repr,
            metadata=metadata or {},
        )
