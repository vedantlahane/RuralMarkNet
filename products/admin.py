"""Admin registrations for products."""
from __future__ import annotations

from django.contrib import admin

from .models import Product


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "farmer",
        "category",
        "price",
        "unit_quantity",
        "unit",
        "quality_grade",
        "available",
    )
    list_filter = ("category", "quality_grade", "farming_practice", "available")
    search_fields = ("name", "farmer__username", "location")
    prepopulated_fields = {"slug": ("name",)}
