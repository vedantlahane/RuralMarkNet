"""Views for user account workflows."""
from __future__ import annotations

from decimal import Decimal
from typing import cast

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LoginView, LogoutView as DjangoLogoutView
from django.db.models import Count, Sum
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect, render
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.utils import formats
from django.utils.translation import gettext_lazy as _
from django.views.decorators.http import require_POST
from django.views.generic import CreateView, ListView, TemplateView

from .forms import LoginForm, ProfileForm, UserRegistrationForm
from .mixins import AdminRequiredMixin, CustomerRequiredMixin, FarmerRequiredMixin
from .models import AuditLog, EmailVerificationToken, User
from .services import EmailVerificationService
from deliveries.models import Delivery
from orders.models import Order, OrderItem
from products.models import Product
from payments.models import Payment


class SignUpView(CreateView):
    """Allow new customers and farmers to register."""

    template_name = "accounts/signup.html"
    form_class = UserRegistrationForm
    success_url = reverse_lazy("accounts:verify-email-pending")

    def form_valid(self, form: UserRegistrationForm) -> HttpResponse:
        user: User = form.save(commit=False)
        user.is_active = False
        user.email_verified = False
        user.save()
        form.save_m2m()
        self.object = user
        EmailVerificationService.send_verification(user, self.request)
        messages.info(
            self.request,
            _(
                "We've sent a verification link. For local testing, copy the URL from the server console."
            ),
        )
        return redirect(self.get_success_url())

    def get_success_url(self) -> str:  # type: ignore[override]
        base_url = super().get_success_url()
        email = getattr(self.object, "email", "") if getattr(self, "object", None) else ""
        if email:
            return f"{base_url}?email={email}"
        return base_url


class RuralLoginView(LoginView):
    """Thin wrapper around Django's authentication view."""

    form_class = LoginForm
    template_name = "accounts/login.html"


class RuralLogoutView(DjangoLogoutView):
    """Re-enable GET requests for logout while keeping Django's logic."""

    http_method_names = ["get", "post", "options"]

    def get(self, request: HttpRequest, *args: object, **kwargs: object) -> HttpResponse:
        # Delegate to the built-in POST handler so session cleanup stays consistent.
        return super().post(request, *args, **kwargs)


class VerificationPendingView(TemplateView):
    """Simple landing page reminding the user to verify their email."""

    template_name = "accounts/verification_pending.html"

    def get_context_data(self, **kwargs: object) -> dict[str, object]:
        context = super().get_context_data(**kwargs)
        email = self.request.GET.get("email") if self.request else ""
        context["email"] = email or ""
        return context


class CurrencyFormattingMixin:
    """Utility mixin that produces locale-aware rupee formatting."""

    def _format_currency(self, value: Decimal) -> str:
        value = value or Decimal("0")
        formatted = formats.number_format(value, decimal_pos=2, use_l10n=True)
        return f"₹{formatted}"


class DashboardBaseView(CurrencyFormattingMixin, TemplateView):
    """Base view providing shared dashboard context and defaults."""

    template_name = "accounts/dashboard.html"

    def get_dashboard_context(self, user: User) -> dict[str, object]:  # pragma: no cover - abstract
        raise NotImplementedError

    def get_context_data(self, **kwargs: object) -> dict[str, object]:
        context = super().get_context_data(**kwargs)
        user = cast(User, self.request.user)
        context["role"] = user.role
        context.update(self.get_dashboard_context(user))
        context.setdefault("orders_title", _("Recent Orders"))
        context.setdefault("orders_subtitle", _("Latest activity from your marketplace."))
        context.setdefault("orders_link_name", "orders:list")
        context.setdefault("orders_cta_label", _("View all orders"))
        context.setdefault("products_title", _("Recent Products"))
        context.setdefault("products_subtitle", _("Fresh items ready for your customers."))
        context.setdefault("products_link_name", "products:list")
        context.setdefault("products_cta_label", _("Browse marketplace"))
        context.setdefault("summary_cards", [])
        context.setdefault("quick_actions", [])
        return context


class DashboardCustomerView(CustomerRequiredMixin, DashboardBaseView):
    """Dashboard for customers highlighting recent orders and deliveries."""

    template_name = "accounts/customer_dashboard.html"

    def get_dashboard_context(self, user: User) -> dict[str, object]:
        orders_qs = (
            Order.objects.filter(customer=user)
            .exclude(status=Order.Status.CART)
            .select_related("delivery")
        )
        recent_orders = list(orders_qs[:5])
        total_orders = orders_qs.count()
        open_orders = orders_qs.exclude(
            status__in=[Order.Status.DELIVERED, Order.Status.CANCELLED]
        ).count()
        total_spent = orders_qs.aggregate(total=Sum("total_amount"))["total"] or Decimal("0")
        next_delivery = (
            Delivery.objects.select_related("order", "assigned_farmer")
            .filter(order__customer=user)
            .exclude(status=Delivery.Status.CANCELLED)
            .order_by("order__scheduled_date", "updated_at")
            .first()
        )
        purchased_product_ids = (
            OrderItem.objects.filter(order__customer=user)
            .values_list("product_id", flat=True)
        )
        recommendations = list(
            Product.objects.filter(available=True)
            .exclude(pk__in=purchased_product_ids)
            .order_by("-created_at")[:5]
        )

        summary_cards = [
            {
                "label": _("Total orders"),
                "value": str(total_orders),
                "helper": _("Completed and in-progress purchases"),
            },
            {
                "label": _("Open orders"),
                "value": str(open_orders),
                "helper": _("Waiting for confirmation or delivery"),
            },
            {
                "label": _("Total spend"),
                "value": self._format_currency(total_spent),
                "helper": _("Across all time"),
            },
            {
                "label": _("Last sign in"),
                "value": formats.date_format(
                    user.last_login, format="SHORT_DATE_FORMAT"
                )
                if user.last_login
                else _("First login"),
                "helper": _("Keep your profile details up to date"),
            },
        ]

        if next_delivery and next_delivery.order.scheduled_date:
            summary_cards[1]["helper"] = _("Next delivery on %(date)s") % {
                "date": formats.date_format(
                    next_delivery.order.scheduled_date, "SHORT_DATE_FORMAT"
                )
            }

        return {
            "orders": recent_orders,
            "products": recommendations,
            "summary_cards": summary_cards,
            "next_delivery": next_delivery,
            "role_badge": _("Customer workspace"),
            "quick_actions": [
                {
                    "label": _("Browse marketplace"),
                    "description": _("Discover fresh produce from partner farmers."),
                    "url": reverse("products:list"),
                    "icon": "🛍️",
                },
                {
                    "label": _("View my cart"),
                    "description": _("Review items waiting for checkout."),
                    "url": reverse("orders:cart"),
                    "icon": "🧺",
                },
                {
                    "label": _("Manage profile"),
                    "description": _("Update contact details and preferences."),
                    "url": reverse("accounts:profile"),
                    "icon": "👤",
                },
            ],
            "orders_title": _("Recent Orders"),
            "orders_subtitle": _("Latest activity from your purchases."),
            "products_title": _("Recommended Products"),
            "products_subtitle": _("Fresh picks based on your activity."),
            "products_cta_label": _("Browse marketplace"),
            "deliveries": list(
                Delivery.objects.select_related("order")
                .filter(order__customer=user)
                .exclude(status=Delivery.Status.CANCELLED)
                .order_by("-updated_at")[:4]
            ),
        }


class DashboardFarmerView(FarmerRequiredMixin, DashboardBaseView):
    """Dashboard for farmers showing product and delivery stats."""

    template_name = "accounts/farmer_dashboard.html"

    def get_dashboard_context(self, user: User) -> dict[str, object]:
        now = timezone.now()
        start_of_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

        products_qs = Product.objects.filter(farmer=user)
        recent_products = list(products_qs.order_by("-updated_at")[:5])
        active_products = products_qs.filter(available=True).count()
        low_stock_qs = products_qs.filter(inventory__lte=10).order_by("inventory", "name")[:5]

        order_items_qs = OrderItem.objects.filter(product__farmer=user)
        revenue_total = order_items_qs.aggregate(total=Sum("line_total"))["total"] or Decimal("0")
        revenue_month = (
            order_items_qs.filter(order__created_at__gte=start_of_month)
            .aggregate(total=Sum("line_total"))["total"]
            or Decimal("0")
        )

        orders_qs = (
            Order.objects.filter(items__product__farmer=user)
            .exclude(status=Order.Status.CART)
            .select_related("customer")
            .prefetch_related("items__product", "delivery")
            .distinct()
        )
        recent_orders = list(orders_qs[:5])
        pending_orders = orders_qs.exclude(
            status__in=[Order.Status.DELIVERED, Order.Status.CANCELLED]
        ).count()

        pending_delivery_count = Delivery.objects.filter(
            assigned_farmer=user,
            status__in=[
                Delivery.Status.PENDING,
                Delivery.Status.SCHEDULED,
                Delivery.Status.IN_TRANSIT,
            ],
        ).count()

        recent_customers = list(
            User.objects.filter(orders__items__product__farmer=user)
            .exclude(pk=user.pk)
            .distinct()
            .order_by("-orders__created_at")[:5]
        )

        summary_cards = [
            {
                "label": _("Active products"),
                "value": str(active_products),
                "helper": _("Visible in the marketplace"),
            },
            {
                "label": _("Pending deliveries"),
                "value": str(pending_delivery_count),
                "helper": _("Deliveries awaiting action"),
            },
            {
                "label": _("Revenue (month)"),
                "value": self._format_currency(revenue_month),
                "helper": _("Current calendar month"),
            },
            {
                "label": _("Revenue (lifetime)"),
                "value": self._format_currency(revenue_total),
                "helper": _("All time sales"),
            },
        ]

        low_stock_alerts = list(low_stock_qs)
        payment_choices = list(Payment.Providers.choices)
        accepted_codes = set(user.get_accepted_payment_methods())
        accepted_labels = [label for code, label in payment_choices if code in accepted_codes]
        using_all_methods = len(accepted_labels) == len(payment_choices)

        return {
            "orders": recent_orders,
            "products": recent_products,
            "summary_cards": summary_cards,
            "inventory_alerts": low_stock_alerts,
            "recent_customers": recent_customers,
            "role_badge": _("Farmer control center"),
            "quick_actions": [
                {
                    "label": _("List new product"),
                    "description": _("Create a listing to reach more customers."),
                    "url": reverse("portal-farmer:products-create"),
                    "icon": "➕",
                },
                {
                    "label": _("Manage catalogue"),
                    "description": _("Edit availability, pricing, and stock."),
                    "url": reverse("portal-farmer:products-list"),
                    "icon": "📦",
                },
                {
                    "label": _("Delivery board"),
                    "description": _("Coordinate schedules with drivers and customers."),
                    "url": reverse("portal-farmer:deliveries-list"),
                    "icon": "🚚",
                },
            ],
            "orders_title": _("Recent Orders"),
            "orders_subtitle": _("Orders that include your produce."),
            "orders_link_name": "portal-farmer:deliveries-list",
            "orders_cta_label": _("Open delivery board"),
            "products_title": _("Your listings"),
            "products_subtitle": _("Recently updated products."),
            "products_link_name": "portal-farmer:products-list",
            "products_cta_label": _("Manage products"),
            "pending_deliveries": pending_delivery_count,
            "low_stock_count": len(low_stock_alerts),
            "accepted_payment_methods": accepted_labels,
            "available_payment_methods": payment_choices,
            "using_all_payment_methods": using_all_methods,
        }


class DashboardAdminView(AdminRequiredMixin, DashboardBaseView):
    """Dashboard for administrators overseeing the marketplace."""

    template_name = "accounts/admin_dashboard.html"

    def get_dashboard_context(self, user: User) -> dict[str, object]:
        now = timezone.now()
        start_of_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

        orders_qs = (
            Order.objects.exclude(status=Order.Status.CART)
            .select_related("customer")
            .prefetch_related("items__product", "delivery")
        )
        recent_orders = list(orders_qs[:5])
        total_orders = orders_qs.count()
        monthly_orders = orders_qs.filter(created_at__gte=start_of_month).count()
        total_gmv = orders_qs.aggregate(total=Sum("total_amount"))["total"] or Decimal("0")

        farmer_count = User.objects.filter(role=User.Roles.FARMER).count()
        customer_count = User.objects.filter(role=User.Roles.CUSTOMER).count()
        active_products = Product.objects.filter(available=True).count()

        top_products = (
            Product.objects.filter(
                orderitem__order__status__in=[
                    Order.Status.CONFIRMED,
                    Order.Status.SHIPPED,
                    Order.Status.DELIVERED,
                ]
            )
            .annotate(purchase_count=Count("orderitem"))
            .order_by("-purchase_count", "name")[:5]
        )

        recent_logs = list(AuditLog.objects.select_related("user")[:6])

        summary_cards = [
            {
                "label": _("Farmers"),
                "value": str(farmer_count),
                "helper": _("Active sellers on the platform"),
            },
            {
                "label": _("Customers"),
                "value": str(customer_count),
                "helper": _("Registered buyers"),
            },
            {
                "label": _("Orders (month)"),
                "value": str(monthly_orders),
                "helper": _("Since %(date)s")
                % {"date": formats.date_format(start_of_month.date(), "SHORT_DATE_FORMAT")},
            },
            {
                "label": _("Gross merchandise value"),
                "value": self._format_currency(total_gmv),
                "helper": _("All time revenue"),
            },
        ]

        return {
            "orders": recent_orders,
            "products": list(top_products),
            "summary_cards": summary_cards,
            "role_badge": _("Administrator overview"),
            "quick_actions": [
                {
                    "label": _("Review orders"),
                    "description": _("Audit transactions and fulfilment status."),
                    "url": reverse("portal-admin:orders-list"),
                    "icon": "🧾",
                },
                {
                    "label": _("Monitor deliveries"),
                    "description": _("Track handoffs happening across the marketplace."),
                    "url": reverse("portal-admin:deliveries-list"),
                    "icon": "🚚",
                },
                {
                    "label": _("Product moderation"),
                    "description": _("Approve or flag product listings."),
                    "url": reverse("portal-admin:products-list"),
                    "icon": "🌿",
                },
            ],
            "orders_title": _("Marketplace Orders"),
            "orders_subtitle": _("Latest transactions across RuralMarkNet."),
            "orders_link_name": "portal-admin:orders-list",
            "orders_cta_label": _("Review orders"),
            "products_title": _("Top products"),
            "products_link_name": "portal-admin:products-list",
            "products_cta_label": _("Review catalogue"),
            "platform_stats": {
                "active_products": active_products,
                "total_orders": total_orders,
                "total_gmv": self._format_currency(total_gmv),
            },
            "recent_logs": recent_logs,
        }


class AdminAuditLogListView(AdminRequiredMixin, ListView):
    """Display recent audit log entries for compliance review."""

    model = AuditLog
    paginate_by = 25
    context_object_name = "logs"
    template_name = "accounts/admin_audit_list.html"

    def get_queryset(self):  # type: ignore[override]
        return AuditLog.objects.select_related("user").all()


class AdminFinancialReportView(AdminRequiredMixin, CurrencyFormattingMixin, TemplateView):
    """Financial reporting view summarising revenue and payment health."""

    template_name = "accounts/admin_financial_report.html"

    def get_context_data(self, **kwargs: object) -> dict[str, object]:
        context = super().get_context_data(**kwargs)
        now = timezone.now()
        start_of_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

        orders_qs = Order.objects.exclude(status=Order.Status.CART)
        total_orders = orders_qs.count()
        total_gmv = orders_qs.aggregate(total=Sum("total_amount"))["total"] or Decimal("0")
        monthly_gmv = (
            orders_qs.filter(created_at__gte=start_of_month)
            .aggregate(total=Sum("total_amount"))["total"]
            or Decimal("0")
        )
        paid_orders = orders_qs.filter(payment_status=Order.PaymentStatus.PAID).count()
        pending_orders = orders_qs.exclude(
            status__in=[Order.Status.DELIVERED, Order.Status.CANCELLED]
        ).count()

        successful_payments = Payment.objects.filter(status=Payment.Status.SUCCESS)
        average_order_value = (total_gmv / total_orders) if total_orders else Decimal("0")

        refund_count = Payment.objects.filter(status=Payment.Status.REFUNDED).count()

        top_products = (
            Product.objects.filter(
                orderitem__order__status__in=[
                    Order.Status.CONFIRMED,
                    Order.Status.SHIPPED,
                    Order.Status.DELIVERED,
                ]
            )
            .annotate(purchase_count=Count("orderitem"))
            .order_by("-purchase_count", "name")[:10]
        )

        context["financials"] = {
            "gmv_total": self._format_currency(total_gmv),
            "gmv_month": self._format_currency(monthly_gmv),
            "orders_total": total_orders,
            "orders_paid": paid_orders,
            "orders_pending": pending_orders,
            "payments_success": successful_payments.count(),
            "payments_refunded": refund_count,
            "average_order_value": self._format_currency(average_order_value),
        }
        context["top_products"] = top_products
        context["recent_logs"] = AuditLog.objects.select_related("user")[:8]
        context["report_generated_at"] = now
        return context


def _default_auth_backend() -> str:
    backends = getattr(settings, "AUTHENTICATION_BACKENDS", [])
    return backends[0] if backends else "django.contrib.auth.backends.ModelBackend"


def verify_email(request: HttpRequest, token: str) -> HttpResponse:
    """Redeem a verification token and activate the matching user."""

    try:
        record = EmailVerificationToken.objects.select_related("user").get(token=token)
    except EmailVerificationToken.DoesNotExist:
        messages.error(request, _("That verification link is no longer valid."))
        return redirect("accounts:login")

    if not record.is_valid():
        if record.is_consumed:
            messages.info(request, _("This email address has already been confirmed."))
        else:
            messages.error(request, _("That verification link has expired. Request a new one below."))
        pending_url = reverse("accounts:verify-email-pending")
        email = record.user.email
        if email:
            pending_url = f"{pending_url}?email={email}"
        return redirect(pending_url)

    user = record.user
    record.mark_consumed()
    user.email_verified = True
    user.is_active = True
    user.save(update_fields=["email_verified", "is_active"])
    user.backend = _default_auth_backend()  # type: ignore[attr-defined]
    login(request, user)
    messages.success(request, _("Email verified! You're all set."))
    return redirect(user.get_dashboard_url())


@require_POST
def resend_verification_email(request: HttpRequest) -> HttpResponse:
    """Allow the user to request another verification link."""

    email = (request.POST.get("email") or "").strip()
    redirect_url = reverse("accounts:verify-email-pending")
    if email:
        redirect_url = f"{redirect_url}?email={email}"

    if not email:
        messages.error(request, _("Enter the email address you used when signing up."))
        return redirect(redirect_url)

    user = User.objects.filter(email__iexact=email).first()
    if user is None:
        messages.error(request, _("We couldn't find an account with that email."))
        return redirect(redirect_url)

    if user.email_verified:
        messages.info(request, _("This email is already verified. You can sign in now."))
        return redirect("accounts:login")

    EmailVerificationService.send_verification(user, request)
    messages.success(request, _("A fresh verification link is on the way."))
    return redirect(redirect_url)


@login_required
def update_profile(request: HttpRequest) -> HttpResponse:
    """Allow users to update their profile details."""

    user = cast(User, request.user)
    if request.method == "POST":
        form = ProfileForm(request.POST, instance=user)
        if form.is_valid():
            form.save()
            messages.success(request, _("Profile updated successfully."))
            return redirect(user.get_dashboard_url())
    else:
        form = ProfileForm(instance=user)
    return render(request, "accounts/profile_form.html", {"form": form})


def redirect_to_role_dashboard(request: HttpRequest) -> HttpResponse:
    """Send the logged-in user to their role-specific dashboard."""

    if not request.user.is_authenticated:
        return redirect("accounts:login")
    user = cast(User, request.user)
    return redirect(user.get_dashboard_url())
