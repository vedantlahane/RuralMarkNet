"""Models for user accounts."""
from __future__ import annotations

from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _


class User(AbstractUser):
    """Custom user model with farmer/customer roles."""

    class Roles(models.TextChoices):
        FARMER = "farmer", _("Farmer")
        CUSTOMER = "customer", _("Customer")
        ADMIN = "admin", _("Administrator")

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
        choices=[("en", "English"), ("hi", "Hindi")],
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
        return f"{self.get_full_name() or self.username} ({self.get_role_display()})"

    def get_dashboard_url(self) -> str:
        """Return the named URL for the user dashboard."""
        if self.is_farmer:
            return "farmer-dashboard"
        if self.is_customer:
            return "customer-dashboard"
        return "dashboard"
