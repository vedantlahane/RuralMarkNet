"""Views for user account workflows."""
from __future__ import annotations

from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LoginView
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect, render
from django.urls import reverse, reverse_lazy
from django.utils.translation import gettext_lazy as _
from django.views.generic import CreateView, TemplateView

from .forms import LoginForm, ProfileForm, UserRegistrationForm
from .models import User


class SignUpView(CreateView[User]):
    """Allow new customers and farmers to register."""

    template_name = "accounts/signup.html"
    form_class = UserRegistrationForm
    success_url = reverse_lazy("dashboard")

    def form_valid(self, form: UserRegistrationForm) -> HttpResponse:
        response = super().form_valid(form)
        login(self.request, self.object)
        messages.success(self.request, _("Welcome to RuralMarkNet!"))
        return response


class RuralLoginView(LoginView):
    """Thin wrapper around Django's authentication view."""

    form_class = LoginForm
    template_name = "accounts/login.html"


class DashboardView(LoginRequiredMixin, TemplateView):
    """Shared dashboard landing page."""

    template_name = "accounts/dashboard.html"

    def get_context_data(self, **kwargs: object) -> dict[str, object]:
        context = super().get_context_data(**kwargs)
        context["role"] = self.request.user.role
        context["orders"] = self.request.user.orders.all()[:5]
        context["products"] = self.request.user.products.all()[:5]
        return context


class CustomerDashboardView(DashboardView):
    """Dashboard for customers highlighting recent orders."""

    template_name = "accounts/customer_dashboard.html"


class FarmerDashboardView(DashboardView):
    """Dashboard for farmers showing product stats."""

    template_name = "accounts/farmer_dashboard.html"


@login_required
def update_profile(request: HttpRequest) -> HttpResponse:
    """Allow users to update their profile details."""

    if request.method == "POST":
        form = ProfileForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, _("Profile updated successfully."))
            return redirect("dashboard")
    else:
        form = ProfileForm(instance=request.user)
    return render(request, "accounts/profile_form.html", {"form": form})


def redirect_to_role_dashboard(request: HttpRequest) -> HttpResponse:
    """Send the logged-in user to their role-specific dashboard."""

    if not request.user.is_authenticated:
        return redirect("login")
    return redirect(request.user.get_dashboard_url())
