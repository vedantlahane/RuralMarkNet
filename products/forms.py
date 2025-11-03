"""Forms for product listings and filters."""
from __future__ import annotations

from django import forms
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
from typing import cast

from accounts.models import User

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
            "unit",
            "unit_quantity",
            "quality_grade",
            "farming_practice",
            "harvest_date",
            "best_before_days",
            "inventory",
            "available",
            "location",
            "storage_instructions",
            "certifications",
            "image",
        )
        widgets = {
            "description": forms.Textarea(attrs={"rows": 4}),
            "storage_instructions": forms.Textarea(attrs={"rows": 3}),
            "harvest_date": forms.DateInput(attrs={"type": "date"}),
        }


class AdminProductForm(ProductForm):
    """Extended form that lets administrators assign farmers."""

    farmer = forms.ModelChoiceField(label=_("Farmer"), queryset=get_user_model().objects.none())

    class Meta(ProductForm.Meta):
        fields = ("farmer",) + ProductForm.Meta.fields

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        user_model = cast("type[User]", get_user_model())
        farmer_field = cast(forms.ModelChoiceField, self.fields["farmer"])
        farmer_field.queryset = user_model.objects.filter(role=User.Roles.FARMER)


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
