"""Admin registration for deliveries."""
from __future__ import annotations

from django.contrib import admin

from .models import Delivery


@admin.register(Delivery)
class DeliveryAdmin(admin.ModelAdmin):
    list_display = ("order", "status", "assigned_farmer", "updated_at")
    list_filter = ("status",)
    search_fields = ("order__id", "assigned_farmer__username")
