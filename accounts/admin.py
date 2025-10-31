"""Admin bindings for accounts."""
from __future__ import annotations

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _

from .models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """Customized admin for the custom user model."""

    fieldsets = BaseUserAdmin.fieldsets + (
        (_("Profile"), {"fields": ("role", "phone_number", "preferred_language", "address")}),
    )
    list_display = ("username", "email", "role", "is_active", "is_staff")
    list_filter = ("role", "is_active", "is_staff")
    search_fields = ("username", "email", "first_name", "last_name")
