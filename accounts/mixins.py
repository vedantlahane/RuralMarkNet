"""Reusable access-control mixins for account roles."""
from __future__ import annotations

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.utils.translation import gettext_lazy as _

from .models import User


class AdminRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    """Allow access only to authenticated administrators."""

    permission_denied_message = _("Administrator access required.")

    def test_func(self) -> bool:  # noqa: D401
        request = getattr(self, "request", None)
        user = getattr(request, "user", None)
        return bool(isinstance(user, User) and user.role == User.Roles.ADMIN)

    def handle_no_permission(self):  # type: ignore[override]
        request = getattr(self, "request", None)
        user = getattr(request, "user", None)
        if request is not None and getattr(user, "is_authenticated", False):
            messages.error(request, self.permission_denied_message)
        return super().handle_no_permission()
