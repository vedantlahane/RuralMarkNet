"""Views for order placement and tracking."""
from __future__ import annotations

from typing import cast

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _
from django.views.generic import DetailView, ListView
from django.views.generic.edit import FormView, UpdateView

from accounts.mixins import AdminRequiredMixin, CustomerRequiredMixin, OwnerRequiredMixin
from accounts.models import AuditLog, User

from products.models import Product

from .forms import AdminOrderUpdateForm, DeliveryScheduleForm
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
    """Add a product to the authenticated user's cart with custom quantity."""

    product = get_object_or_404(Product, pk=product_id, available=True)
    user = cast(User, request.user)
    if not getattr(user, "is_customer", False):
        messages.error(request, _("Only customers can modify carts."))
        return redirect(user.get_dashboard_url())

    cart = _get_or_create_cart(request)

    quantity_source = request.POST if request.method == "POST" else request.GET
    raw_quantity = quantity_source.get("quantity", "1") if quantity_source else "1"

    try:
        quantity = int(raw_quantity)
    except (TypeError, ValueError):
        quantity = 1

    if quantity < 1:
        quantity = 1

    if product.inventory <= 0:
        messages.warning(request, _("%(product)s is currently out of stock." ) % {"product": product.name})
        return redirect(product.get_absolute_url())

    try:
        item = OrderItem.objects.get(order=cart, product=product)
        created = False
    except OrderItem.DoesNotExist:
        item = OrderItem(order=cart, product=product, quantity=0, price=product.price)
        created = True

    current_quantity = item.quantity
    max_additional = max(product.inventory - current_quantity, 0)

    if max_additional <= 0:
        messages.info(
            request,
            _("You already have the maximum available quantity of %(product)s in your cart." )
            % {"product": product.name},
        )
        return redirect("orders:cart")

    add_quantity = min(quantity, max_additional)

    item.price = product.price
    item.quantity = current_quantity + add_quantity

    if created:
        item.save()
    else:
        item.save(update_fields=["quantity", "price"])

    if add_quantity > 1:
        message = _("Added %(count)d units of %(product)s to your cart.") % {
            "count": add_quantity,
            "product": product.name,
        }
    else:
        message = _("%(product)s added to your cart.") % {"product": product.name}

    if add_quantity < quantity:
        message += " " + _("Only %(count)d units were available right now.") % {
            "count": add_quantity,
        }

    messages.success(request, message)

    return redirect("orders:cart")


class CartView(CustomerRequiredMixin, ListView):
    """Display the items currently in the cart."""

    template_name = "orders/cart.html"
    context_object_name = "items"

    def get_queryset(self):  # type: ignore[override]
        self.cart = _get_or_create_cart(self.request)
        return self.cart.items.select_related("product")  # type: ignore[attr-defined]

    def get_context_data(self, **kwargs):  # type: ignore[override]
        context = super().get_context_data(**kwargs)
        context["cart"] = self.cart
        context["schedule_form"] = DeliveryScheduleForm()
        return context


class CheckoutView(CustomerRequiredMixin, FormView):
    """Finalize the order after capturing delivery preferences."""

    form_class = DeliveryScheduleForm
    template_name = "orders/checkout.html"
    success_url = reverse_lazy("orders:list")

    def dispatch(self, request: HttpRequest, *args: object, **kwargs: object):
        self.cart = _get_or_create_cart(request)
        if not self.cart.items.exists():  # type: ignore[attr-defined]
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
        AuditLog.record(
            user=cast(User, self.request.user),
            action=_("Checkout completed"),
            instance=self.cart,
            metadata={
                "scheduled_date": (
                    form.cleaned_data["scheduled_date"].isoformat()
                    if form.cleaned_data["scheduled_date"]
                    else None
                ),
                "total_amount": str(self.cart.total_amount),
            },
        )
        return super().form_valid(form)


class OrderListView(CustomerRequiredMixin, ListView):
    """List orders for the logged-in customer."""

    template_name = "orders/order_list.html"
    context_object_name = "orders"

    def get_queryset(self):  # type: ignore[override]
        return Order.objects.filter(customer=self.request.user).exclude(
            status=Order.Status.CART
        )


class OrderDetailView(CustomerRequiredMixin, OwnerRequiredMixin, DetailView):
    """Detailed view of a single order."""

    template_name = "orders/order_detail.html"
    context_object_name = "order"
    owner_field = "customer"

    def get_queryset(self):  # type: ignore[override]
        return Order.objects.filter(customer=self.request.user)


class AdminOrderListView(AdminRequiredMixin, ListView):
    """Platform-wide order list for administrators."""

    template_name = "orders/admin_order_list.html"
    context_object_name = "orders"
    paginate_by = 25

    def get_queryset(self):  # type: ignore[override]
        return (
            Order.objects.exclude(status=Order.Status.CART)
            .select_related("customer")
            .prefetch_related("items__product")
            .order_by("-created_at")
        )


class AdminOrderUpdateView(AdminRequiredMixin, UpdateView):
    """Allow administrators to update order status and scheduling details."""

    form_class = AdminOrderUpdateForm
    template_name = "orders/admin_order_form.html"
    context_object_name = "order"
    success_url = reverse_lazy("portal-admin:orders-list")

    def get_queryset(self):  # type: ignore[override]
        return Order.objects.exclude(status=Order.Status.CART).select_related("customer")

    def form_valid(self, form):  # type: ignore[override]
        messages.success(self.request, _("Order updated."))
        response = super().form_valid(form)
        order = cast(Order, getattr(self, "object", form.instance))
        actor = cast(User, self.request.user)
        AuditLog.record(
            user=actor,
            action=_("Order status updated"),
            instance=order,
            metadata={
                "status": order.status,
                "payment_status": order.payment_status,
            },
        )
        return response

    def get_context_data(self, **kwargs):  # type: ignore[override]
        context = super().get_context_data(**kwargs)
        context["items"] = self.object.items.select_related("product")  # type: ignore[attr-defined]
        return context
