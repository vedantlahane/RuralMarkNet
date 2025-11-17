"""Admin bindings for accounts."""
from __future__ import annotations

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _

from .models import EmailVerificationToken, User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """Customized admin for the custom user model."""

    fieldsets = tuple(
        list(BaseUserAdmin.fieldsets)
        + [
            (
                _("Profile"),
                {
                    "fields": (
                        "role",
                        "phone_number",
                        "preferred_language",
                        "address",
                        "email_verified",
                    )
                },
            )
        ]
    )
    list_display = ("username", "email", "role", "email_verified", "is_active", "is_staff")
    list_filter = ("role", "email_verified", "is_active", "is_staff")
    search_fields = ("username", "email", "first_name", "last_name")


@admin.register(EmailVerificationToken)
class EmailVerificationTokenAdmin(admin.ModelAdmin):
    list_display = ("user", "token", "created_at", "expires_at", "consumed_at")
    search_fields = ("user__username", "user__email", "token")
    list_filter = ("consumed_at",)
