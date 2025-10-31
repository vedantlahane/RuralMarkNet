"""Views for order placement and tracking."""
from __future__ import annotations

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _
from django.views.generic import DetailView, ListView
from django.views.generic.edit import FormView

from products.models import Product

from .forms import DeliveryScheduleForm
from .models import Order, OrderItem


def _get_or_create_cart(request: HttpRequest) -> Order:
    """Retrieve the user's cart or create a new one."""
    order_id = request.session.get("cart_id")
    if order_id:
        try:
            return Order.objects.get(
                pk=order_id,
                customer=request.user,
                status=Order.Status.CART,
            )
        except Order.DoesNotExist:
            pass
    cart = Order.objects.create(customer=request.user)
    request.session["cart_id"] = cart.pk
    return cart


@login_required
def add_to_cart(request: HttpRequest, product_id: int) -> HttpResponse:
    """Add a product to the authenticated user's cart."""
    product = get_object_or_404(Product, pk=product_id, available=True)
    cart = _get_or_create_cart(request)
    item, created = OrderItem.objects.get_or_create(
        order=cart,
        product=product,
        defaults={"price": product.price, "quantity": 1},
    )
    if not created:
        item.quantity += 1
        item.save(update_fields=["quantity"])
    cart.recalculate_total()
    messages.success(request, _("Product added to your cart."))
    return redirect("orders:cart")


class CartView(LoginRequiredMixin, ListView):
    """Display the items currently in the cart."""

    template_name = "orders/cart.html"
    context_object_name = "items"

    def get_queryset(self):  # type: ignore[override]
        self.cart = _get_or_create_cart(self.request)
        return self.cart.items.select_related("product")

    def get_context_data(self, **kwargs):  # type: ignore[override]
        context = super().get_context_data(**kwargs)
        context["cart"] = self.cart
        context["schedule_form"] = DeliveryScheduleForm()
        return context


class CheckoutView(LoginRequiredMixin, FormView):
    """Finalize the order after capturing delivery preferences."""

    form_class = DeliveryScheduleForm
    template_name = "orders/checkout.html"
    success_url = reverse_lazy("orders:list")

    def dispatch(self, request: HttpRequest, *args: object, **kwargs: object):
        self.cart = _get_or_create_cart(request)
        if not self.cart.items.exists():
            messages.warning(request, _("Your cart is empty."))
            return redirect("products:list")
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form: DeliveryScheduleForm) -> HttpResponse:
        self.cart.delivery_address = form.cleaned_data["delivery_address"]
        self.cart.scheduled_date = form.cleaned_data["scheduled_date"]
        self.cart.scheduled_window = form.cleaned_data["scheduled_window"]
        self.cart.notes = form.cleaned_data.get("notes", "")
        self.cart.status = Order.Status.PENDING
        self.cart.save()
        self.request.session.pop("cart_id", None)
        messages.success(self.request, _("Order placed successfully."))
        return super().form_valid(form)


class OrderListView(LoginRequiredMixin, ListView):
    """List orders for the logged-in customer."""

    template_name = "orders/order_list.html"
    context_object_name = "orders"

    def get_queryset(self):  # type: ignore[override]
        return Order.objects.filter(customer=self.request.user).exclude(
            status=Order.Status.CART
        )


class OrderDetailView(LoginRequiredMixin, DetailView):
    """Detailed view of a single order."""

    template_name = "orders/order_detail.html"
    context_object_name = "order"

    def get_queryset(self):  # type: ignore[override]
        return Order.objects.filter(customer=self.request.user)
