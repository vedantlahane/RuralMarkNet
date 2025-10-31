"""Admin registrations for products."""
from __future__ import annotations

from django.contrib import admin

from .models import Product


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("name", "farmer", "category", "price", "available")
    list_filter = ("category", "available")
    search_fields = ("name", "farmer__username")
    prepopulated_fields = {"slug": ("name",)}
