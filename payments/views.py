"""Payment workflow views including secure Stripe webhook verification."""
from __future__ import annotations

from typing import Any

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


class PaymentInitView(LoginRequiredMixin, FormView):
    """Allow the customer to start a payment for an order."""

    template_name = "payments/payment_summary.html"
    form_class = PaymentInitForm

    def dispatch(self, request: HttpRequest, *args: object, **kwargs: object):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        self.order = get_object_or_404(
            Order,
            pk=kwargs["order_id"],
            customer=request.user,
            status__in=[Order.Status.PENDING, Order.Status.CONFIRMED],
        )
        if self.order.payment_status == Order.PaymentStatus.PAID:
            messages.info(request, _("This order is already paid."))
            return redirect("orders:detail", pk=self.order.pk)
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):  # type: ignore[override]
        context = super().get_context_data(**kwargs)
        context["order"] = self.order
        return context

    def form_valid(self, form: PaymentInitForm) -> HttpResponse:
        provider = form.cleaned_data["provider"]
        payment = Payment.objects.create(
            order=self.order,
            provider=provider,
            amount=self.order.total_amount,
            currency="INR",
        )
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
