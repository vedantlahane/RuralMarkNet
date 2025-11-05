"""Payment workflow views including secure Stripe webhook verification."""
from __future__ import annotations

from typing import Any, Iterable, cast

import stripe

if hasattr(stripe, "error") and hasattr(stripe.error, "SignatureVerificationError"):  # type: ignore[attr-defined]
    SignatureVerificationError = stripe.error.SignatureVerificationError  # type: ignore[attr-defined]
else:  # pragma: no cover - defensive fallback when stripe's error module is unavailable
    class SignatureVerificationError(Exception):
        """Fallback exception used when Stripe's error module is unavailable."""

        pass
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpRequest, HttpResponse, HttpResponseBadRequest, HttpResponseForbidden, JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _
from django.views import View
from django.views.generic.edit import FormView

from orders.models import Order

from .forms import PaymentInitForm
from .models import Payment
from .services import dispatch_payment
from accounts.models import AuditLog, User


class PaymentInitView(LoginRequiredMixin, FormView):
    """Allow the customer to start a payment for an order."""

    template_name = "payments/payment_summary.html"
    form_class = PaymentInitForm

    def dispatch(self, request: HttpRequest, *args: object, **kwargs: object):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        order_qs = (
            Order.objects.filter(
                pk=kwargs["order_id"],
                customer=request.user,
                status__in=[Order.Status.PENDING, Order.Status.CONFIRMED],
            )
            .select_related()
            .prefetch_related("items__product__farmer")
        )
        self.order = get_object_or_404(order_qs)
        if self.order.payment_status == Order.PaymentStatus.PAID:
            messages.info(request, _("This order is already paid."))
            return redirect("orders:detail", pk=self.order.pk)
        self._prepare_provider_choices()
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):  # type: ignore[override]
        context = super().get_context_data(**kwargs)
        context["order"] = self.order
        context["available_methods"] = getattr(self, "_provider_choices", Payment.Providers.choices)
        context["restricted_methods"] = getattr(self, "_restricted_provider_choices", [])
        context["using_default_methods"] = getattr(self, "_using_default_methods", False)
        return context

    def get_form_kwargs(self) -> dict[str, Any]:  # type: ignore[override]
        kwargs = super().get_form_kwargs()
        kwargs["allowed_providers"] = getattr(self, "_provider_choices", Payment.Providers.choices)
        return kwargs

    def _prepare_provider_choices(self) -> None:
        all_choices = list(Payment.Providers.choices)
        default_codes = {code for code, _ in all_choices}
        order_items_manager = getattr(self.order, "items", None)
        farmers: set[Any] = set()
        if order_items_manager is not None:
            for item in order_items_manager.all():
                product = getattr(item, "product", None)
                farmer = getattr(product, "farmer", None)
                if farmer is not None:
                    farmers.add(farmer)
        allowed_codes = set(default_codes)
        for farmer in farmers:
            if hasattr(farmer, "get_accepted_payment_methods"):
                allowed_codes &= set(farmer.get_accepted_payment_methods())

        self._restricted_provider_choices = [
            (code, label) for code, label in all_choices if code not in allowed_codes
        ]

        if not allowed_codes:
            self._using_default_methods = True
            self._provider_choices = all_choices
            self._restricted_provider_choices = []
        else:
            self._using_default_methods = False
            filtered = [(code, label) for code, label in all_choices if code in allowed_codes]
            self._provider_choices = filtered or all_choices

    def form_valid(self, form: PaymentInitForm) -> HttpResponse:
        provider = form.cleaned_data["provider"]
        payment = Payment.objects.create(
            order=self.order,
            provider=provider,
            amount=self.order.total_amount,
            currency="INR",
        )
        if provider == Payment.Providers.COD:
            payment.status = Payment.Status.INITIATED
            payment.save(update_fields=["status"])

            order_fields: list[str] = []
            if self.order.status == Order.Status.PENDING:
                self.order.status = Order.Status.CONFIRMED
                order_fields.append("status")
            if self.order.payment_status != Order.PaymentStatus.UNPAID:
                self.order.payment_status = Order.PaymentStatus.UNPAID
                order_fields.append("payment_status")
            if order_fields:
                self.order.save(update_fields=order_fields)

            audit_user = cast(User | None, self.request.user if self.request.user.is_authenticated else None)
            AuditLog.record(
                user=audit_user,
                action=_("Cash on delivery selected"),
                instance=self.order,
                metadata={"payment_id": payment.pk},
            )
            messages.success(
                self.request,
                _("Cash on delivery confirmed. Please prepare exact change at delivery."),
            )
            return redirect("orders:detail", pk=self.order.pk)

        session = dispatch_payment(self.order, provider)
        messages.info(
            self.request,
            _("Redirecting to %(provider)s for secure payment...")
            % {"provider": provider.capitalize()},
        )
        return redirect(session.redirect_url)


class StripeWebhookView(View):
    """Handle incoming Stripe webhook events with signature verification.

    Requires STRIPE_WEBHOOK_SECRET in Django settings.
    """

    def post(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        try:
            payload = request.body.decode("utf-8")
        except UnicodeDecodeError:
            return HttpResponseBadRequest("Invalid payload encoding")

        sig_header = request.META.get("HTTP_STRIPE_SIGNATURE")
        webhook_secret = getattr(settings, "STRIPE_WEBHOOK_SECRET", None)
        if webhook_secret is None:
            return HttpResponseForbidden("Webhook secret not configured")
        if not sig_header:
            return HttpResponseBadRequest("Missing signature header")

        try:
            event = stripe.Webhook.construct_event(payload, sig_header, webhook_secret)
        except (ValueError, SignatureVerificationError):
            return HttpResponseForbidden("Invalid signature")

        # Safe, centralised handling of Stripe events can be placed here. Keep this small.
        data_object = event.get("data", {}).get("object", {})
        payment_id = data_object.get("metadata", {}).get("payment_id")
        transaction_id = data_object.get("id")

        if payment_id:
            try:
                payment = get_object_or_404(Payment, pk=payment_id)
                payment.mark_successful(transaction_id or "", data_object)
            except Exception:
                # Keep webhook endpoint robust; don't leak errors to Stripe
                return HttpResponse(status=200)

        return JsonResponse({"status": "received"})


class PaymentResultView(LoginRequiredMixin, View):
    """Display payment outcomes based on provider callbacks."""

    def get(self, request: HttpRequest, *args: object, **kwargs: object) -> HttpResponse:
        messages.success(request, _("Payment processed. Check your order summary."))
        return redirect("orders:detail", pk=kwargs["order_id"])
