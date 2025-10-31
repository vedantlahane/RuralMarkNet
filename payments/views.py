"""Payment workflow views."""
from __future__ import annotations

import json

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpRequest, HttpResponse, HttpResponseBadRequest, JsonResponse
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
    """Handle incoming Stripe webhook events (mock implementation)."""

    def post(self, request: HttpRequest, *args: object, **kwargs: object) -> HttpResponse:
        payload = json.loads(request.body)
        transaction_id = payload.get("data", {}).get("object", {}).get("id")
        payment_id = payload.get("data", {}).get("object", {}).get("metadata", {}).get("payment_id")
        if not transaction_id or not payment_id:
            return HttpResponseBadRequest("Invalid payload")
        payment = get_object_or_404(Payment, pk=payment_id)
        payment.mark_successful(transaction_id, payload)
        return JsonResponse({"status": "received"})


class PaymentResultView(LoginRequiredMixin, View):
    """Display payment outcomes based on provider callbacks."""

    def get(self, request: HttpRequest, *args: object, **kwargs: object) -> HttpResponse:
        messages.success(request, _("Payment processed. Check your order summary."))
        return redirect("orders:detail", pk=kwargs["order_id"])
