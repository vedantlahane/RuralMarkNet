"""Views for product catalogue and management."""
from __future__ import annotations

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.db.models import Q
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _
from django.views.generic import DetailView, ListView
from django.views.generic.edit import CreateView, UpdateView

from .forms import ProductFilterForm, ProductForm
from .models import Product


class ProductListView(ListView):
    """Display available products with filtering options."""

    model = Product
    paginate_by = 12
    template_name = "products/product_list.html"
    context_object_name = "products"

    def get_queryset(self):  # type: ignore[override]
        queryset = super().get_queryset().select_related("farmer")
        form = ProductFilterForm(self.request.GET)
        if form.is_valid():
            search = form.cleaned_data.get("search")
            if search:
                queryset = queryset.filter(
                    Q(name__icontains=search)
                    | Q(description__icontains=search)
                    | Q(farmer__first_name__icontains=search)
                )
            category = form.cleaned_data.get("category")
            if category:
                queryset = queryset.filter(category=category)
            min_price = form.cleaned_data.get("min_price")
            if min_price:
                queryset = queryset.filter(price__gte=min_price)
            max_price = form.cleaned_data.get("max_price")
            if max_price:
                queryset = queryset.filter(price__lte=max_price)
            available = form.cleaned_data.get("available")
            if available:
                queryset = queryset.filter(available=True)
        return queryset


class ProductDetailView(DetailView):
    """Display a single product."""

    model = Product
    template_name = "products/product_detail.html"
    context_object_name = "product"
    slug_field = "slug"


class FarmerRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    """Ensure the logged-in user is a farmer."""

    def test_func(self) -> bool:
        return bool(self.request.user.is_authenticated and self.request.user.is_farmer)

    def handle_no_permission(self):  # type: ignore[override]
        messages.error(self.request, _("You need a farmer account to manage listings."))
        return super().handle_no_permission()


class ProductCreateView(FarmerRequiredMixin, CreateView):
    """Allow farmers to add new products."""

    form_class = ProductForm
    template_name = "products/product_form.html"

    def form_valid(self, form: ProductForm):  # type: ignore[override]
        form.instance.farmer = self.request.user
        messages.success(self.request, _("Product created successfully."))
        return super().form_valid(form)


class ProductUpdateView(FarmerRequiredMixin, UpdateView):
    """Allow farmers to update an existing product."""

    form_class = ProductForm
    template_name = "products/product_form.html"
    slug_field = "slug"

    def get_queryset(self):  # type: ignore[override]
        return Product.objects.filter(farmer=self.request.user)

    def form_valid(self, form):  # type: ignore[override]
        messages.success(self.request, _("Product updated successfully."))
        return super().form_valid(form)


class FarmerProductListView(FarmerRequiredMixin, ListView):
    """List of products owned by the logged-in farmer."""

    template_name = "products/farmer_product_list.html"

    def get_queryset(self):  # type: ignore[override]
        return Product.objects.filter(farmer=self.request.user)

    def get_context_data(self, **kwargs):  # type: ignore[override]
        context = super().get_context_data(**kwargs)
        context["create_url"] = reverse_lazy("products:create")
        return context
