"""Reusable access-control mixins for account roles."""
from __future__ import annotations

from typing import Any

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.shortcuts import redirect
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from .models import User


class RoleRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    """Base mixin enforcing an authenticated role with friendly messaging."""

    permission_denied_message = _("You do not have access to this section.")
    login_url = "accounts:login"

    def handle_no_permission(self):  # type: ignore[override]
        request = getattr(self, "request", None)
        if request is not None and getattr(request, "user", None) is not None:
            user = request.user
            if getattr(user, "is_authenticated", False):
                messages.error(request, self.permission_denied_message)
        return super().handle_no_permission()


class AdminRequiredMixin(RoleRequiredMixin):
    """Allow access only to authenticated administrators."""

    permission_denied_message = _("Administrator access required.")

    def test_func(self) -> bool:  # noqa: D401
        request = getattr(self, "request", None)
        user = getattr(request, "user", None)
        return bool(
            getattr(user, "is_authenticated", False)
            and (getattr(user, "is_staff", False) or getattr(user, "is_superuser", False))
        )


class FarmerRequiredMixin(RoleRequiredMixin):
    """Ensure the logged-in user is a farmer."""

    permission_denied_message = _("Farmer access required.")

    def test_func(self) -> bool:  # noqa: D401
        request = getattr(self, "request", None)
        user = getattr(request, "user", None)
        return bool(getattr(user, "is_authenticated", False) and getattr(user, "is_farmer", False))


class CustomerRequiredMixin(RoleRequiredMixin):
    """Ensure the logged-in user is a marketplace customer."""

    permission_denied_message = _("Customer account required.")

    def test_func(self) -> bool:  # noqa: D401
        request = getattr(self, "request", None)
        user = getattr(request, "user", None)
        return bool(
            getattr(user, "is_authenticated", False)
            and getattr(user, "is_customer", False)
            and not getattr(user, "is_staff", False)
        )


class OwnerRequiredMixin(LoginRequiredMixin):
    """Ensure the requesting user owns the object unless they are staff."""

    owner_field = "user"
    allow_staff_override = True
    permission_denied_message = _("You do not have permission to modify this record.")

    def get_owner_from_object(self, obj: Any) -> Any:
        """Return the owner attribute configured via ``owner_field``."""

        owner = getattr(obj, self.owner_field, None)
        return owner() if callable(owner) else owner

    def get_permission_denied_redirect(self) -> str:
        """Return a sensible default redirect when ownership fails."""

        return reverse("accounts:switch-dashboard")

    def handle_no_permission(self):  # type: ignore[override]
        request = getattr(self, "request", None)
        if request is not None and getattr(request, "user", None) is not None:
            if request.user.is_authenticated:
                messages.error(request, self.permission_denied_message)
                return redirect(self.get_permission_denied_redirect())
        return super().handle_no_permission()

    def dispatch(self, request, *args, **kwargs):  # type: ignore[override]
        if not request.user.is_authenticated:
            return self.handle_no_permission()

        self._ownership_cached_object = self.get_object()  # type: ignore[attr-defined]
        if self.allow_staff_override and request.user.is_staff:
            return super().dispatch(request, *args, **kwargs)

        owner = self.get_owner_from_object(self._ownership_cached_object)
        if owner != request.user:
            return self.handle_no_permission()
        return super().dispatch(request, *args, **kwargs)

    def get_object(self, queryset=None):  # type: ignore[override]
        if hasattr(self, "_ownership_cached_object"):
            return self._ownership_cached_object
        obj = super().get_object(queryset)  # type: ignore[misc]
        self._ownership_cached_object = obj
        return obj
