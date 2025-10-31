"""Integration helpers for payment providers."""
from __future__ import annotations

from dataclasses import dataclass

from orders.models import Order
from .models import Payment


@dataclass
class PaymentSession:
    """Simple DTO for redirecting the user to a gateway."""

    provider: str
    redirect_url: str
    client_secret: str | None = None
def create_stripe_session(order: Order) -> PaymentSession:
    """Create a Stripe checkout session (placeholder implementation)."""
    # In production, call stripe.checkout.Session.create here.
    return PaymentSession(
        provider=Payment.Providers.STRIPE,
        redirect_url="https://checkout.stripe.com/pay/mock-session",
        client_secret="mock_client_secret",
    )


def create_paypal_order(order: Order) -> PaymentSession:
    """Create a PayPal order (placeholder implementation)."""
    return PaymentSession(
        provider=Payment.Providers.PAYPAL,
        redirect_url="https://www.paypal.com/checkoutnow?token=mock-token",
    )


def dispatch_payment(order: Order, provider: str) -> PaymentSession:
    """Route to the appropriate provider helper."""
    if provider == Payment.Providers.STRIPE:
        return create_stripe_session(order)
    if provider == Payment.Providers.PAYPAL:
        return create_paypal_order(order)
    raise ValueError("Unsupported provider")
