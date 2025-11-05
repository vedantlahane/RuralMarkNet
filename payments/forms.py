"""Forms for initiating payments."""
from __future__ import annotations

from typing import Any, Iterable

from django import forms
from django.utils.translation import gettext_lazy as _

from .models import Payment


class PaymentInitForm(forms.Form):
    """Let the customer choose a provider before redirect."""

    provider = forms.ChoiceField(choices=Payment.Providers.choices, label=_("Payment provider"))

    def __init__(
        self,
        *args: Any,
        allowed_providers: Iterable[tuple[str, str]] | None = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(*args, **kwargs)
        if allowed_providers is not None:
            self.fields["provider"].choices = allowed_providers
