"""Views for managing deliveries."""
from __future__ import annotations

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.db.models import Q
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _
from django.views.generic import DetailView, ListView
from django.views.generic.edit import UpdateView

from .forms import DeliveryUpdateForm
from .models import Delivery


class DeliveryListView(LoginRequiredMixin, ListView):
    """Deliveries visible to customers and assigned farmers."""

    template_name = "deliveries/delivery_list.html"
    context_object_name = "deliveries"

    def get_queryset(self):  # type: ignore[override]
        user = self.request.user
        return Delivery.objects.filter(
            Q(order__customer=user) | Q(assigned_farmer=user)
        ).select_related("order", "order__customer")


class DeliveryDetailView(LoginRequiredMixin, DetailView):
    """Detailed delivery tracking view."""

    template_name = "deliveries/delivery_detail.html"
    context_object_name = "delivery"

    def get_queryset(self):  # type: ignore[override]
        user = self.request.user
        return Delivery.objects.filter(
            Q(order__customer=user) | Q(assigned_farmer=user)
        )


class FarmerOnlyMixin(UserPassesTestMixin):
    """Ensure the user can modify the delivery (assigned farmer)."""

    def test_func(self) -> bool:
        delivery: Delivery = self.get_object()  # type: ignore[assignment]
        return bool(
            self.request.user.is_authenticated
            and self.request.user.is_farmer
            and delivery.assigned_farmer_id == self.request.user.id
        )

    def handle_no_permission(self):  # type: ignore[override]
        messages.error(self.request, _("You are not allowed to update this delivery."))
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
