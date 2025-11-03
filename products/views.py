"""Views for product catalogue, management and localisation."""
from __future__ import annotations

from typing import Any

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.db.models import Q
from django.http import HttpRequest, HttpResponse
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator
from django.utils.translation import check_for_language, gettext_lazy as _
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.views.generic import DetailView, ListView, View
from django.views.generic.edit import CreateView, UpdateView
from django.views.i18n import set_language as django_set_language

from orders.forms import AddToCartForm

from accounts.mixins import AdminRequiredMixin

from .forms import AdminProductForm, ProductFilterForm, ProductForm
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


class FarmerRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    """Ensure the logged-in user is a farmer."""

    def test_func(self) -> bool:
        request = getattr(self, "request", None)
        user = getattr(request, "user", None)
        return bool(getattr(user, "is_authenticated", False) and getattr(user, "is_farmer", False))

    def handle_no_permission(self):  # type: ignore[override]
        request = getattr(self, "request", None)
        if request is not None:
            messages.error(request, _("You need a farmer account to manage listings."))
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
    success_url = reverse_lazy("products:admin-manage")

    def get_queryset(self):  # type: ignore[override]
        return Product.objects.select_related("farmer")

    def form_valid(self, form):  # type: ignore[override]
        messages.success(self.request, _("Product updated."))
        return super().form_valid(form)
