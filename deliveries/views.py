"""Views for managing deliveries."""
from __future__ import annotations

from typing import Any

from django.contrib import messages
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _
from django.views.generic import DetailView, ListView
from django.views.generic.edit import UpdateView

from accounts.mixins import AdminRequiredMixin, CustomerRequiredMixin, FarmerRequiredMixin, OwnerRequiredMixin

from .forms import DeliveryUpdateForm
from .models import Delivery


class BaseDeliveryListView(ListView):
    """Base list view with shared template configuration."""

    template_name = "deliveries/delivery_list.html"
    context_object_name = "deliveries"
    paginate_by = 20

    detail_url_name: str

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:  # type: ignore[override]
        context = super().get_context_data(**kwargs)
        context["detail_url_name"] = self.detail_url_name
        return context


class AdminDeliveryListView(AdminRequiredMixin, BaseDeliveryListView):
    """Administrators can browse every delivery."""

    detail_url_name = "portal-admin:deliveries-detail"

    def get_queryset(self):  # type: ignore[override]
        return (
            Delivery.objects.select_related("order", "order__customer", "assigned_farmer")
            .prefetch_related("order__items__product")
            .order_by("-updated_at")
        )


class AdminDeliveryDetailView(AdminRequiredMixin, DetailView):
    """Administrator detail view for deliveries."""

    template_name = "deliveries/delivery_detail.html"
    context_object_name = "delivery"

    def get_queryset(self):  # type: ignore[override]
        return (
            Delivery.objects.select_related("order", "order__customer", "assigned_farmer")
            .prefetch_related("order__items__product")
        )


class FarmerDeliveryListView(FarmerRequiredMixin, BaseDeliveryListView):
    """Show deliveries assigned to the logged-in farmer."""

    detail_url_name = "portal-farmer:deliveries-detail"

    def get_queryset(self):  # type: ignore[override]
        return (
            Delivery.objects.select_related("order", "order__customer")
            .prefetch_related("order__items__product")
            .filter(assigned_farmer=self.request.user)
            .order_by("-updated_at")
        )


class FarmerDeliveryDetailView(FarmerRequiredMixin, OwnerRequiredMixin, DetailView):
    """Allow farmers to inspect deliveries they are responsible for."""

    template_name = "deliveries/delivery_detail.html"
    context_object_name = "delivery"
    owner_field = "assigned_farmer"

    def get_queryset(self):  # type: ignore[override]
        return (
            Delivery.objects.select_related("order", "order__customer")
            .prefetch_related("order__items__product")
        )

    def get_permission_denied_redirect(self) -> str:  # type: ignore[override]
        return reverse_lazy("portal-farmer:deliveries-list")

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:  # type: ignore[override]
        context = super().get_context_data(**kwargs)
        context.setdefault("update_url_name", "portal-farmer:deliveries-update")
        return context


class FarmerDeliveryUpdateView(FarmerRequiredMixin, OwnerRequiredMixin, UpdateView):
    """Allow the assigned farmer to update delivery progress."""

    form_class = DeliveryUpdateForm
    template_name = "deliveries/delivery_form.html"
    owner_field = "assigned_farmer"
    success_url = reverse_lazy("portal-farmer:deliveries-list")

    def get_queryset(self):  # type: ignore[override]
        return Delivery.objects.select_related("order")

    def form_valid(self, form):  # type: ignore[override]
        messages.success(self.request, _("Delivery updated."))
        return super().form_valid(form)

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:  # type: ignore[override]
        context = super().get_context_data(**kwargs)
        context["cancel_url"] = str(reverse_lazy("portal-farmer:deliveries-list"))
        return context


class CustomerDeliveryListView(CustomerRequiredMixin, BaseDeliveryListView):
    """Customers can monitor their delivery history."""

    detail_url_name = "deliveries:detail"

    def get_queryset(self):  # type: ignore[override]
        return (
            Delivery.objects.select_related("order", "assigned_farmer")
            .prefetch_related("order__items__product")
            .filter(order__customer=self.request.user)
            .exclude(status=Delivery.Status.CANCELLED)
            .order_by("-updated_at")
        )


class CustomerDeliveryDetailView(CustomerRequiredMixin, DetailView):
    """Detailed delivery view for customers."""

    template_name = "deliveries/delivery_detail.html"
    context_object_name = "delivery"

    def get_queryset(self):  # type: ignore[override]
        return (
            Delivery.objects.select_related("order", "assigned_farmer")
            .prefetch_related("order__items__product")
            .filter(order__customer=self.request.user)
        )
