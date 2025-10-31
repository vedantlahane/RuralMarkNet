"""Forms for delivery assignments."""
from __future__ import annotations

from django import forms

from .models import Delivery


class DeliveryUpdateForm(forms.ModelForm):
    """Allow farmers to update delivery progress."""

    class Meta:
        model = Delivery
        fields = ("status", "driver_name", "contact_number")
