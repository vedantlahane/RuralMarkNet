"""URL patterns for the accounts app."""
from __future__ import annotations

from django.contrib.auth.views import PasswordChangeView
from django.urls import path, reverse_lazy

from .views import (
    CustomerDashboardView,
    FarmerDashboardView,
    RuralLoginView,
    RuralLogoutView,
    SignUpView,
    DashboardView,
    redirect_to_role_dashboard,
    update_profile,
)

app_name = "accounts"

urlpatterns = [
    path("signup/", SignUpView.as_view(), name="signup"),
    path("login/", RuralLoginView.as_view(), name="login"),
    path("logout/", RuralLogoutView.as_view(next_page="products:home"), name="logout"),
    path("profile/", update_profile, name="profile"),
    path("switch-dashboard/", redirect_to_role_dashboard, name="switch-dashboard"),
    path("dashboard/", DashboardView.as_view(), name="dashboard"),
    path("dashboard/customer/", CustomerDashboardView.as_view(), name="customer-dashboard"),
    path("dashboard/farmer/", FarmerDashboardView.as_view(), name="farmer-dashboard"),
    path(
        "password-change/",
        PasswordChangeView.as_view(success_url=reverse_lazy("accounts:dashboard")),
        name="password_change",
    ),
]
