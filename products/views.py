"""Views for product catalogue, management and localisation."""
from __future__ import annotations

from typing import Any, cast

from django.contrib import messages
from django.db.models import Q
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator
from django.utils.translation import check_for_language, gettext_lazy as _
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.views.generic import DetailView, ListView, View
from django.views.generic.edit import CreateView, FormView, UpdateView
from django.views.i18n import set_language as django_set_language

from orders.forms import AddToCartForm

from accounts.mixins import AdminRequiredMixin, FarmerRequiredMixin
from accounts.models import AuditLog, User

from .forms import (
    AdminProductForm,
    FarmerInventoryUpdateForm,
    ProductFilterForm,
    ProductForm,
    ProductModerationForm,
)
from .models import Product


@method_decorator(csrf_exempt, name="dispatch")
@method_decorator(require_POST, name="dispatch")
class LanguageSwitchView(View):
    """Ensure language changes also persist to the session for dashboard users."""

    def post(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        response = django_set_language(request)

        if not hasattr(request, "session"):
            return response

        lang_code = request.POST.get("language")
        if not lang_code or not check_for_language(lang_code):
            return response

        request.session["django_language"] = lang_code
        request.session.save()

        return response


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

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:  # type: ignore[override]
        context = super().get_context_data(**kwargs)
        product = context.get("product")
        form = AddToCartForm(initial={"quantity": 1})
        if product is not None:
            max_quantity = getattr(product, "inventory", None)
            if max_quantity is not None and max_quantity > 0:
                form.fields["quantity"].widget.attrs["max"] = max_quantity
        context["add_to_cart_form"] = form
        return context


class ProductCreateView(FarmerRequiredMixin, CreateView):
    """Allow farmers to add new products."""

    form_class = ProductForm
    template_name = "products/product_form.html"

    def form_valid(self, form: ProductForm):  # type: ignore[override]
        form.instance.farmer = self.request.user
        messages.success(self.request, _("Product created successfully."))
        return super().form_valid(form)

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:  # type: ignore[override]
        context = super().get_context_data(**kwargs)
        context["cancel_url"] = str(reverse_lazy("portal-farmer:products-list"))
        return context


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

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:  # type: ignore[override]
        context = super().get_context_data(**kwargs)
        context["cancel_url"] = str(reverse_lazy("portal-farmer:products-list"))
        return context


class FarmerProductListView(FarmerRequiredMixin, ListView):
    """List of products owned by the logged-in farmer."""

    template_name = "products/farmer_product_list.html"

    def get_queryset(self):  # type: ignore[override]
        return Product.objects.filter(farmer=self.request.user)

    def get_context_data(self, **kwargs):  # type: ignore[override]
        context = super().get_context_data(**kwargs)
        context["create_url"] = reverse_lazy("portal-farmer:products-create")
        return context


class FarmerInventoryLowListView(FarmerRequiredMixin, ListView):
    """Highlight products that need restocking for the current farmer."""

    template_name = "products/farmer_inventory_low.html"
    context_object_name = "products"
    paginate_by = 20

    def get_queryset(self):  # type: ignore[override]
        threshold = self.get_threshold()
        return (
            Product.objects.filter(farmer=self.request.user, inventory__lte=threshold)
            .order_by("inventory", "name")
        )

    def get_threshold(self) -> int:
        return 10

    def get_context_data(self, **kwargs):  # type: ignore[override]
        context = super().get_context_data(**kwargs)
        context["threshold"] = self.get_threshold()
        context["update_url"] = reverse_lazy("portal-farmer:inventory-update")
        return context


class FarmerInventoryBulkUpdateView(FarmerRequiredMixin, FormView):
    """Allow farmers to post inventory updates in bulk."""

    form_class = FarmerInventoryUpdateForm
    template_name = "products/farmer_inventory_update.html"
    success_url = reverse_lazy("portal-farmer:inventory-low")

    def get_form_kwargs(self):  # type: ignore[override]
        kwargs = super().get_form_kwargs()
        kwargs["farmer"] = self.request.user
        return kwargs

    def form_valid(self, form: FarmerInventoryUpdateForm) -> HttpResponse:  # type: ignore[override]
        updates = form.cleaned_data["inventory_payload"]
        updated_count = 0
        for product, inventory in updates:
            product.inventory = inventory
            product.save(update_fields=["inventory", "updated_at"])
            updated_count += 1

        AuditLog.record(
            user=cast(User, self.request.user),
            action=_("Inventory bulk update"),
            metadata={
                "count": updated_count,
                "products": [product.pk for product, _ in updates],
            },
        )

        messages.success(
            self.request,
            _( "Updated inventory for %(count)d product(s)." )
            % {"count": updated_count},
        )
        return super().form_valid(form)


class AdminProductListView(AdminRequiredMixin, ListView):
    """Allow administrators to audit and manage all products."""

    template_name = "products/admin_product_list.html"
    context_object_name = "products"

    def get_queryset(self):  # type: ignore[override]
        return Product.objects.select_related("farmer").order_by("-updated_at")


class AdminProductUpdateView(AdminRequiredMixin, UpdateView):
    """Enable administrators to modify any product listing."""

    form_class = AdminProductForm
    template_name = "products/product_form.html"
    slug_field = "slug"
    success_url = reverse_lazy("portal-admin:products-list")

    def get_queryset(self):  # type: ignore[override]
        return Product.objects.select_related("farmer")

    def form_valid(self, form):  # type: ignore[override]
        messages.success(self.request, _("Product updated."))
        response = super().form_valid(form)
        product = cast(Product, getattr(self, "object", form.instance))
        AuditLog.record(
            user=cast(User, self.request.user),
            action=_("Product updated by administrator"),
            instance=product,
            metadata={"changed_fields": list(form.changed_data)},
        )
        return response

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:  # type: ignore[override]
        context = super().get_context_data(**kwargs)
        context["cancel_url"] = str(reverse_lazy("portal-admin:products-list"))
        return context


class ProductModerationView(AdminRequiredMixin, FormView):
    """Approve or reject a product listing with an audit trail."""

    form_class = ProductModerationForm
    template_name = "products/product_moderation_form.html"
    success_url = reverse_lazy("portal-admin:products-list")

    def dispatch(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:  # type: ignore[override]
        self.product = get_object_or_404(Product.objects.select_related("farmer"), slug=kwargs["slug"])
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:  # type: ignore[override]
        context = super().get_context_data(**kwargs)
        context["product"] = self.product
        return context

    def form_valid(self, form: ProductModerationForm) -> HttpResponse:  # type: ignore[override]
        metadata = form.apply(self.product)
        AuditLog.record(
            user=cast(User, self.request.user),
            action=_("Product moderation"),
            instance=self.product,
            metadata=metadata,
        )
        decision = metadata.get("decision")
        if decision == "approve":
            messages.success(
                self.request,
                _("Product '%(name)s' approved and is now visible.") % {"name": self.product.name},
            )
        else:
            messages.warning(
                self.request,
                _("Product '%(name)s' has been hidden from the catalogue.") % {"name": self.product.name},
            )
        return super().form_valid(form)
