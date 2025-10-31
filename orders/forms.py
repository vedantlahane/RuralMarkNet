"""Forms for managing orders and scheduling deliveries."""
from __future__ import annotations

from django import forms
from django.utils.translation import gettext_lazy as _


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
