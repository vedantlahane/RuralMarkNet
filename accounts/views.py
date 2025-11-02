"""Views for user account workflows."""
from __future__ import annotations

from typing import cast

from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LoginView, LogoutView as DjangoLogoutView
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _
from django.views.generic import CreateView, TemplateView

from .forms import LoginForm, ProfileForm, UserRegistrationForm
from .models import User
from deliveries.models import Delivery
from orders.models import Order
from products.models import Product


class SignUpView(CreateView):
    """Allow new customers and farmers to register."""

    template_name = "accounts/signup.html"
    form_class = UserRegistrationForm
    success_url = reverse_lazy("accounts:dashboard")

    def form_valid(self, form: UserRegistrationForm) -> HttpResponse:
        user: User = form.save()
        login(self.request, user)
        messages.success(self.request, _("Welcome to RuralMarkNet!"))
        return redirect(self.get_success_url())


class RuralLoginView(LoginView):
    """Thin wrapper around Django's authentication view."""

    form_class = LoginForm
    template_name = "accounts/login.html"


class RuralLogoutView(DjangoLogoutView):
    """Re-enable GET requests for logout while keeping Django's logic."""

    http_method_names = ["get", "post", "options"]

    def get(self, request: HttpRequest, *args: object, **kwargs: object) -> HttpResponse:
        # Delegate to the built-in POST handler so session cleanup stays consistent.
        return super().post(request, *args, **kwargs)


class DashboardView(LoginRequiredMixin, TemplateView):
    """Shared dashboard landing page."""

    template_name = "accounts/dashboard.html"

    def get_context_data(self, **kwargs: object) -> dict[str, object]:
        context = super().get_context_data(**kwargs)
        user = cast(User, self.request.user)
        context["role"] = user.role
        context["orders"] = Order.objects.filter(customer=user)[:5]
        context["products"] = Product.objects.filter(farmer=user)[:5]
        return context


class CustomerDashboardView(DashboardView):
    """Dashboard for customers highlighting recent orders."""

    template_name = "accounts/customer_dashboard.html"

    def get_context_data(self, **kwargs: object) -> dict[str, object]:
        context = super().get_context_data(**kwargs)
        customer = cast(User, self.request.user)
        context["deliveries"] = (
            Delivery.objects.select_related("order")
            .filter(order__customer=customer)
            .order_by("-updated_at")[:4]
        )
        return context


class FarmerDashboardView(DashboardView):
    """Dashboard for farmers showing product stats."""

    template_name = "accounts/farmer_dashboard.html"

    def get_context_data(self, **kwargs: object) -> dict[str, object]:
        context = super().get_context_data(**kwargs)
        farmer = cast(User, self.request.user)
        context["pending_deliveries"] = Delivery.objects.filter(
            assigned_farmer=farmer,
            status__in=[
                Delivery.Status.PENDING,
                Delivery.Status.SCHEDULED,
                Delivery.Status.IN_TRANSIT,
            ],
        ).count()
        context["low_stock_count"] = Product.objects.filter(
            farmer=farmer, inventory__lte=10
        ).count()
        return context


@login_required
def update_profile(request: HttpRequest) -> HttpResponse:
    """Allow users to update their profile details."""

    user = cast(User, request.user)
    if request.method == "POST":
        form = ProfileForm(request.POST, instance=user)
        if form.is_valid():
            form.save()
            messages.success(request, _("Profile updated successfully."))
            return redirect("accounts:dashboard")
    else:
        form = ProfileForm(instance=user)
    return render(request, "accounts/profile_form.html", {"form": form})


def redirect_to_role_dashboard(request: HttpRequest) -> HttpResponse:
    """Send the logged-in user to their role-specific dashboard."""

    if not request.user.is_authenticated:
        return redirect("accounts:login")
    user = cast(User, request.user)
    return redirect(user.get_dashboard_url())
