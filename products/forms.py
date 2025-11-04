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


class FarmerInventoryUpdateForm(forms.Form):
    """Accept a JSON payload mapping product IDs to new inventory values."""

    inventory_payload = forms.JSONField(
        label=_("Inventory updates"),
        help_text=_("Provide a JSON object where keys are product IDs and values are new stock counts."),
    )

    def __init__(self, *args, farmer: User, **kwargs):
        self.farmer = farmer
        super().__init__(*args, **kwargs)

    def clean_inventory_payload(self):
        payload = self.cleaned_data["inventory_payload"]
        if not isinstance(payload, dict):
            raise forms.ValidationError(_("Invalid format. Expected an object mapping product IDs to quantities."))

        cleaned_ids: dict[int, int] = {}
        for raw_product_id, raw_quantity in payload.items():
            try:
                product_id = int(raw_product_id)
                quantity = int(raw_quantity)
            except (TypeError, ValueError):
                raise forms.ValidationError(_("Product IDs and quantities must be integers."))
            if quantity < 0:
                raise forms.ValidationError(_("Quantities must be zero or positive."))
            cleaned_ids[product_id] = quantity

        products = list(Product.objects.filter(pk__in=cleaned_ids.keys(), farmer=self.farmer))
        missing_ids = set(cleaned_ids.keys()) - {product.pk for product in products}
        if missing_ids:
            raise forms.ValidationError(
                _("You can only update inventory for your own products. Invalid IDs: %(ids)s")
                % {"ids": ", ".join(str(pk) for pk in sorted(missing_ids))}
            )

        updates: list[tuple[Product, int]] = [(product, cleaned_ids[product.pk]) for product in products]
        return updates


class ProductModerationForm(forms.Form):
    """Allow administrators to approve or reject product listings."""

    decision = forms.ChoiceField(
        label=_("Decision"),
        choices=[
            ("approve", _("Approve listing")),
            ("reject", _("Reject listing")),
        ],
        widget=forms.RadioSelect,
    )
    note = forms.CharField(
        label=_("Moderator note"),
        required=False,
        widget=forms.Textarea(attrs={"rows": 4}),
        help_text=_("Optional details that will be stored in the audit log."),
    )

    def apply(self, product: Product) -> dict[str, object]:
        """Persist moderation decision on the product and return metadata."""

        decision = self.cleaned_data["decision"]
        product.available = decision == "approve"
        product.save(update_fields=["available", "updated_at"])
        return {
            "decision": decision,
            "note": self.cleaned_data.get("note", ""),
            "product_id": product.pk,
        }
