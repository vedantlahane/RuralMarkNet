"""Forms for initiating payments."""
from __future__ import annotations

from django import forms
from django.utils.translation import gettext_lazy as _

from .models import Payment


class PaymentInitForm(forms.Form):
    """Let the customer choose a provider before redirect."""

    provider = forms.ChoiceField(choices=Payment.Providers.choices, label=_("Payment provider"))
