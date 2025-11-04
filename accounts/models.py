"""Models for user accounts."""
from __future__ import annotations

from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _


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
