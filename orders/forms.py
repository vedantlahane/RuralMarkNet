"""Forms for managing orders and scheduling deliveries."""
from __future__ import annotations

from typing import Iterable

from django import forms
from django.utils.translation import gettext_lazy as _

from payments.models import Payment

from .models import Order


class AddToCartForm(forms.Form):
    """Collect customer preferences before adding an item to the cart."""

    quantity = forms.IntegerField(
        min_value=1,
        initial=1,
        label=_("Quantity"),
        help_text=_("Number of units you want to add to your basket."),
        widget=forms.NumberInput(attrs={
            "min": 1,
            "step": 1,
            "class": (
                "mt-2 w-full rounded-2xl border border-slate-200 px-4 py-3 text-sm "
                "text-slate-800 shadow-sm focus:border-emerald-500 focus:outline-none "
                "focus:ring-2 focus:ring-emerald-200"
            ),
        }),
    )



class DeliveryScheduleForm(forms.Form):
    """Customer-facing delivery scheduling form."""

    delivery_address = forms.CharField(widget=forms.Textarea, label=_("Delivery address"))
    scheduled_date = forms.DateField(widget=forms.DateInput(attrs={"type": "date"}))
    scheduled_window = forms.ChoiceField(
        choices=[
            ("morning", _("Morning")),
            ("afternoon", _("Afternoon")),
            ("evening", _("Evening")),
        ],
        label=_("Preferred slot"),
    )
    notes = forms.CharField(required=False, widget=forms.Textarea, label=_("Notes"))
    payment_provider = forms.ChoiceField(
        choices=Payment.Providers.choices,
        label=_("Payment method"),
        help_text=_("This is the method you will use to pay for this order."),
    )

    def __init__(
        self,
        *args,
        allowed_providers: Iterable[tuple[str, str]] | None = None,
        **kwargs,
    ) -> None:
        super().__init__(*args, **kwargs)
        choices = list(allowed_providers) if allowed_providers is not None else list(Payment.Providers.choices)
        if not choices:
            choices = list(Payment.Providers.choices)
        self.fields["payment_provider"].choices = choices
        self._allowed_provider_codes = {code for code, _ in choices}

        input_classes = (
            "mt-2 w-full rounded-2xl border border-slate-200 px-4 py-3 text-sm "
            "text-slate-800 shadow-sm focus:border-emerald-500 focus:outline-none "
            "focus:ring-2 focus:ring-emerald-200"
        )
        for name, field in self.fields.items():
            existing_class = field.widget.attrs.get("class", "")
            merged = f"{existing_class} {input_classes}".strip()
            field.widget.attrs["class"] = merged
            field.widget.attrs.setdefault("placeholder", field.label)
            if name == "scheduled_date":
                # Date inputs already set type="date"; keep placeholder simple.
                field.widget.attrs.setdefault("placeholder", field.label)

    def clean_payment_provider(self) -> str:
        provider = self.cleaned_data.get("payment_provider", "")
        if provider not in self._allowed_provider_codes:
            raise forms.ValidationError(_("Selected payment method is not available for this order."))
        return provider


class AdminOrderUpdateForm(forms.ModelForm):
    """Allow administrators to adjust order details."""

    class Meta:
        model = Order
        fields = (
            "status",
            "payment_status",
            "delivery_address",
            "scheduled_date",
            "scheduled_window",
            "notes",
        )
        widgets = {
            "delivery_address": forms.Textarea,
            "notes": forms.Textarea,
            "scheduled_date": forms.DateInput(attrs={"type": "date"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        input_classes = (
            "mt-2 w-full rounded-2xl border border-slate-200 px-4 py-3 text-sm "
            "text-slate-800 shadow-sm focus:border-emerald-500 focus:outline-none "
            "focus:ring-2 focus:ring-emerald-200"
        )
        for name, field in self.fields.items():
            existing_class = field.widget.attrs.get("class", "")
            field.widget.attrs["class"] = f"{existing_class} {input_classes}".strip()
            field.widget.attrs.setdefault("placeholder", field.label)
