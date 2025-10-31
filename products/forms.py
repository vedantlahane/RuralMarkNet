"""Forms for product listings and filters."""
from __future__ import annotations

from django import forms
from django.utils.translation import gettext_lazy as _

from .models import Product


class ProductForm(forms.ModelForm):
    """Create or update a product listing."""

    class Meta:
        model = Product
        fields = (
            "name",
            "category",
            "description",
            "price",
            "inventory",
            "available",
            "location",
            "image",
        )


class ProductFilterForm(forms.Form):
    """Filtering controls shown on the product list."""

    search = forms.CharField(required=False, label=_("Search"))
    category = forms.ChoiceField(
        required=False,
        choices=[("", _("All categories"))] + list(Product.Categories.choices),
    )
    min_price = forms.DecimalField(required=False, min_value=0, label=_("Min price"))
    max_price = forms.DecimalField(required=False, min_value=0, label=_("Max price"))
    available = forms.BooleanField(required=False, initial=True, label=_("In stock"))
