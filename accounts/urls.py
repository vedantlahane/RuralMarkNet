"""URL patterns for the accounts app."""
from __future__ import annotations

from django.contrib.auth.views import PasswordChangeView
from django.urls import path, reverse_lazy

from .views import (
    DashboardCustomerView,
    RuralLoginView,
    RuralLogoutView,
    SignUpView,
    VerificationPendingView,
    redirect_to_role_dashboard,
    resend_verification_email,
    update_profile,
    verify_email,
)

app_name = "accounts"

urlpatterns = [
    path("signup/", SignUpView.as_view(), name="signup"),
    path("verify/pending/", VerificationPendingView.as_view(), name="verify-email-pending"),
    path("verify/<str:token>/", verify_email, name="verify-email"),
    path("verify/resend/", resend_verification_email, name="verify-email-resend"),
    path("login/", RuralLoginView.as_view(), name="login"),
    path("logout/", RuralLogoutView.as_view(next_page="products:home"), name="logout"),
    path("profile/", update_profile, name="profile"),
    path("switch-dashboard/", redirect_to_role_dashboard, name="switch-dashboard"),
    path("dashboard/", DashboardCustomerView.as_view(), name="customer-dashboard"),
    path(
        "password-change/",
        PasswordChangeView.as_view(success_url=reverse_lazy("accounts:switch-dashboard")),
        name="password_change",
    ),
]
