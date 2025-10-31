"""Context processors for product filters."""
from __future__ import annotations

from .forms import ProductFilterForm
from .models import Product


def product_filters(request):
    """Expose filter form and categories globally."""
    return {
        "product_filter_form": ProductFilterForm(request.GET or None),
        "product_categories": Product.Categories.choices,
    }
