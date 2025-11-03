"""Views for managing deliveries."""
from __future__ import annotations

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.db.models import Q
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _
from django.views.generic import DetailView, ListView
from django.views.generic.edit import UpdateView

from accounts.models import User

from .forms import DeliveryUpdateForm
from .models import Delivery


class DeliveryListView(LoginRequiredMixin, ListView):
    """Deliveries visible to customers and assigned farmers."""

    template_name = "deliveries/delivery_list.html"
    context_object_name = "deliveries"

    def get_queryset(self):  # type: ignore[override]
        user = self.request.user
        if getattr(user, "role", None) == User.Roles.ADMIN:
            return Delivery.objects.select_related("order", "order__customer", "assigned_farmer")
        return Delivery.objects.filter(
            Q(order__customer=user) | Q(assigned_farmer=user)
        ).select_related("order", "order__customer")


class DeliveryDetailView(LoginRequiredMixin, DetailView):
    """Detailed delivery tracking view."""

    template_name = "deliveries/delivery_detail.html"
    context_object_name = "delivery"

    def get_queryset(self):  # type: ignore[override]
        user = self.request.user
        if getattr(user, "role", None) == User.Roles.ADMIN:
            return Delivery.objects.all()
        return Delivery.objects.filter(
            Q(order__customer=user) | Q(assigned_farmer=user)
        )


class FarmerOnlyMixin(UserPassesTestMixin):
    """Ensure the user can modify the delivery (assigned farmer)."""

    def test_func(self) -> bool:
        delivery: Delivery = self.get_object()  # type: ignore[assignment]
        request = getattr(self, "request", None)
        user = getattr(request, "user", None)
        if getattr(user, "role", None) == User.Roles.ADMIN:
            return True
        return bool(
            getattr(user, "is_authenticated", False)
            and getattr(user, "is_farmer", False)
            and getattr(delivery, "assigned_farmer_id", None) == getattr(user, "id", None)
        )

    def handle_no_permission(self):  # type: ignore[override]
        request = getattr(self, "request", None)
        if request is not None:
            messages.error(request, _("You are not allowed to update this delivery."))
        return super().handle_no_permission()


class DeliveryUpdateView(LoginRequiredMixin, FarmerOnlyMixin, UpdateView):
    """Allow assigned farmers to update delivery status."""

    form_class = DeliveryUpdateForm
    template_name = "deliveries/delivery_form.html"
    success_url = reverse_lazy("deliveries:list")

    def get_queryset(self):  # type: ignore[override]
        return Delivery.objects.select_related("order")

    def form_valid(self, form):  # type: ignore[override]
        messages.success(self.request, _("Delivery updated."))
        return super().form_valid(form)
