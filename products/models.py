"""Product catalog models."""
from __future__ import annotations

from decimal import Decimal
from typing import Any

from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models
from django.urls import reverse
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _


class Product(models.Model):
    """Represents a marketplace listing."""

    class Categories(models.TextChoices):
        VEGETABLES = "vegetables", _("Vegetables")
        FRUITS = "fruits", _("Fruits")
        DAIRY = "dairy", _("Dairy")
        GRAINS = "grains", _("Grains")
        OTHERS = "others", _("Others")

    class Units(models.TextChoices):
        KILOGRAM = "kg", _("Kilogram")
        GRAM = "g", _("Gram")
        LITRE = "l", _("Litre")
        PIECE = "piece", _("Piece")
        BUNCH = "bunch", _("Bunch")

    class QualityGrades(models.TextChoices):
        PREMIUM = "premium", _("Premium grade")
        STANDARD = "standard", _("Standard grade")
        ECONOMY = "economy", _("Economy grade")

    class FarmingPractices(models.TextChoices):
        ORGANIC = "organic", _("Organic")
        NATURAL = "natural", _("Natural")
        CONVENTIONAL = "conventional", _("Conventional")
        HYDROPONIC = "hydroponic", _("Hydroponic")

    name = models.CharField(max_length=255)
    slug = models.SlugField(unique=True, blank=True)
    farmer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="products",
    )
    category = models.CharField(max_length=32, choices=Categories.choices)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=8, decimal_places=2)
    unit = models.CharField(
        max_length=16,
        choices=Units.choices,
        default=Units.KILOGRAM,
        help_text=_("Measurement customers will see when ordering."),
    )
    unit_quantity = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        default=Decimal("1.00"),
        validators=[MinValueValidator(Decimal("0.01"))],
        help_text=_("Amount of produce included per unit."),
    )
    quality_grade = models.CharField(
        max_length=32,
        choices=QualityGrades.choices,
        default=QualityGrades.STANDARD,
        help_text=_("Visible quality grade to reassure buyers."),
    )
    farming_practice = models.CharField(
        max_length=32,
        choices=FarmingPractices.choices,
        default=FarmingPractices.CONVENTIONAL,
        help_text=_("Primary growing method used."),
    )
    harvest_date = models.DateField(blank=True, null=True, help_text=_("Optional harvest date for traceability."))
    best_before_days = models.PositiveSmallIntegerField(
        blank=True,
        null=True,
        help_text=_("Number of days the produce stays at peak quality."),
    )
    inventory = models.PositiveIntegerField(default=0)
    available = models.BooleanField(default=True)
    location = models.CharField(max_length=128, blank=True)
    storage_instructions = models.TextField(blank=True, help_text=_("Tips customers should follow after delivery."))
    certifications = models.CharField(
        max_length=255,
        blank=True,
        help_text=_("Organic, FPO or other certification names."),
    )
    image = models.ImageField(upload_to="products/", blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]
        verbose_name = _("Product")
        verbose_name_plural = _("Products")

    def save(self, *args: Any, **kwargs: Any) -> None:
        if not self.slug:
            farmer_reference = getattr(self, "farmer_id", None)
            if farmer_reference is None and hasattr(self, "farmer"):
                farmer_reference = getattr(self.farmer, "pk", "")
            self.slug = slugify(f"{self.name}-{farmer_reference or ''}")
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        return self.name

    def get_absolute_url(self) -> str:
        return reverse("products:detail", kwargs={"slug": self.slug})
