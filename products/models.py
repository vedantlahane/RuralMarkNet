"""Product catalog models."""
from __future__ import annotations

from django.conf import settings
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
    inventory = models.PositiveIntegerField(default=0)
    available = models.BooleanField(default=True)
    location = models.CharField(max_length=128, blank=True)
    image = models.ImageField(upload_to="products/", blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]
        verbose_name = _("Product")
        verbose_name_plural = _("Products")

    def save(self, *args: object, **kwargs: object) -> None:
        if not self.slug:
            self.slug = slugify(f"{self.name}-{self.farmer_id}")
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        return self.name

    def get_absolute_url(self) -> str:
        return reverse("products:detail", kwargs={"slug": self.slug})
