"""Admin registration for payments."""
from __future__ import annotations

from django.contrib import admin

from .models import Payment


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ("order", "provider", "status", "amount", "created_at")
    list_filter = ("provider", "status")
    search_fields = ("transaction_id", "order__id")
