"""Management command to populate the database with sample data."""
from __future__ import annotations

from datetime import timedelta
from decimal import Decimal
from typing import TYPE_CHECKING, cast

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from deliveries.models import Delivery
from orders.models import Order, OrderItem
from payments.models import Payment
from products.models import Product

if TYPE_CHECKING:  # pragma: no cover - type checking only
    from accounts.models import User as CustomUser


class Command(BaseCommand):
    help = "Create deterministic sample data for local development and demos."

    DEFAULT_PASSWORD = "Passw0rd!"

    def handle(self, *args, **options) -> None:  # noqa: D401
        """Entrypoint for the command."""

        self.stdout.write("Seeding sample data...")

        with transaction.atomic():
            self.users: dict[str, "CustomUser"] = {}
            self.products: dict[str, Product] = {}

            self._create_users()
            self._create_products()
            self._create_orders()

        self.stdout.write(self.style.SUCCESS("Sample data ready."))

    # ------------------------------------------------------------------
    # User creation helpers
    # ------------------------------------------------------------------
    def _create_users(self) -> None:
        user_model = cast("type[CustomUser]", get_user_model())

        farmer_data = [
            {
                "username": "farmer_amit",
                "password": self.DEFAULT_PASSWORD,
                "first_name": "Amit",
                "last_name": "Patil",
                "email": "amit.patil@example.com",
                "role": user_model.Roles.FARMER,
                "preferred_language": "hi",
                "phone_number": "+91-9876543210",
                "address": "Village Road, Nashik, Maharashtra",
            },
            {
                "username": "farmer_sunita",
                "password": self.DEFAULT_PASSWORD,
                "first_name": "Sunita",
                "last_name": "Deshmukh",
                "email": "sunita.deshmukh@example.com",
                "role": user_model.Roles.FARMER,
                "preferred_language": "mr",
                "phone_number": "+91-9988776655",
                "address": "Green Farm, Pune, Maharashtra",
            },
            {
                "username": "farmer_priya",
                "password": self.DEFAULT_PASSWORD,
                "first_name": "Priya",
                "last_name": "Gadekar",
                "email": "priya.gadekar@example.com",
                "role": user_model.Roles.FARMER,
                "preferred_language": "en",
                "phone_number": "+91-9654321890",
                "address": "Sunrise Fields, Aurangabad, Maharashtra",
            },
            {
                "username": "farmer_kiran",
                "password": self.DEFAULT_PASSWORD,
                "first_name": "Kiran",
                "last_name": "Sawant",
                "email": "kiran.sawant@example.com",
                "role": user_model.Roles.FARMER,
                "preferred_language": "hi",
                "phone_number": "+91-9765432187",
                "address": "Riverbank Farm, Kolhapur, Maharashtra",
            },
        ]

        customer_data = [
            {
                "username": "customer_riya",
                "password": self.DEFAULT_PASSWORD,
                "first_name": "Riya",
                "last_name": "Sharma",
                "email": "riya.sharma@example.com",
                "role": user_model.Roles.CUSTOMER,
                "preferred_language": "en",
                "phone_number": "+91-9123456780",
                "address": "Apartment 3B, Mumbai, Maharashtra",
            },
            {
                "username": "customer_dev",
                "password": self.DEFAULT_PASSWORD,
                "first_name": "Dev",
                "last_name": "Kulkarni",
                "email": "dev.kulkarni@example.com",
                "role": user_model.Roles.CUSTOMER,
                "preferred_language": "mr",
                "phone_number": "+91-9345678123",
                "address": "Sector 21, Nagpur, Maharashtra",
            },
        ]

        staff_data = [
            {
                "username": "market_admin",
                "password": self.DEFAULT_PASSWORD,
                "first_name": "Admin",
                "last_name": "User",
                "email": "admin@example.com",
                "role": user_model.Roles.ADMIN,
                "preferred_language": "en",
                "is_staff": True,
                "is_superuser": True,
            },
            {
                "username": "operations_admin",
                "password": self.DEFAULT_PASSWORD,
                "first_name": "Operations",
                "last_name": "Lead",
                "email": "ops.admin@example.com",
                "role": user_model.Roles.ADMIN,
                "preferred_language": "en",
                "is_staff": True,
                "is_superuser": False,
            }
        ]

        for dataset in (farmer_data, customer_data, staff_data):
            for entry in dataset:
                payload = entry.copy()
                password = payload.pop("password")
                username = payload["username"]
                defaults = {key: value for key, value in payload.items() if key != "username"}

                user, created = user_model.objects.get_or_create(username=username, defaults=defaults)

                password_updated = False
                if created:
                    user.set_password(password)
                    user.save()
                    action = "created"
                    password_updated = True
                else:
                    action = "found"
                    updated_fields: list[str] = []
                    for field, value in defaults.items():
                        if getattr(user, field, None) != value:
                            setattr(user, field, value)
                            updated_fields.append(field)
                    if updated_fields:
                        user.save(update_fields=updated_fields)
                if not password_updated and not user.check_password(password):
                    user.set_password(password)
                    user.save(update_fields=["password"])
                self.stdout.write(f"  User {username} {action}.")
                self.users[username] = user

    # ------------------------------------------------------------------
    # Product helpers
    # ------------------------------------------------------------------
    def _create_products(self) -> None:
        product_specs = [
            {
                "name": "Organic Tomatoes",
                "farmer": "farmer_amit",
                "category": Product.Categories.VEGETABLES,
                "description": "Vine-ripened tomatoes harvested this morning.",
                "price": Decimal("45.00"),
                "inventory": 120,
                "available": True,
                "location": "Nashik",
            },
            {
                "name": "Alphonso Mangoes",
                "farmer": "farmer_sunita",
                "category": Product.Categories.FRUITS,
                "description": "Sweet Alphonso mangoes from Ratnagiri farms.",
                "price": Decimal("150.00"),
                "inventory": 80,
                "available": True,
                "location": "Ratnagiri",
            },
            {
                "name": "Fresh Paneer",
                "farmer": "farmer_amit",
                "category": Product.Categories.DAIRY,
                "description": "Homemade paneer prepared using organic milk.",
                "price": Decimal("220.00"),
                "inventory": 40,
                "available": True,
                "location": "Nashik",
            },
            {
                "name": "Multi-grain Flour",
                "farmer": "farmer_sunita",
                "category": Product.Categories.GRAINS,
                "description": "Stone-ground flour with a balanced grain mix.",
                "price": Decimal("80.00"),
                "inventory": 200,
                "available": True,
                "location": "Pune",
            },
        ]

        for spec in product_specs:
            farmer_key = spec["farmer"]
            farmer = self.users.get(farmer_key)
            if farmer is None:
                raise CommandError(f"Missing user '{farmer_key}'. Run user seeding first.")
            defaults = {key: value for key, value in spec.items() if key not in {"farmer", "name"}}
            product, created = Product.objects.update_or_create(
                farmer=farmer,
                name=spec["name"],
                defaults=defaults,
            )
            product_key = f"{spec['name']}::{spec['farmer']}"
            self.products[product_key] = product
            farmer_username = getattr(farmer, "username", farmer_key)
            self.stdout.write(
                f"  Product '{product.name}' {'created' if created else 'updated'} for {farmer_username}."
            )

    # ------------------------------------------------------------------
    # Order helpers
    # ------------------------------------------------------------------
    def _create_orders(self) -> None:
        now = timezone.now()
        three_days_from_now = now.date() + timedelta(days=3)
        five_days_from_now = now.date() + timedelta(days=5)

        order_specs = [
            {
                "customer": "customer_riya",
                "notes": "Sample order 1",
                "status": Order.Status.CONFIRMED,
                "payment_status": Order.PaymentStatus.PAID,
                "delivery_address": "Apartment 3B, Mumbai, Maharashtra",
                "scheduled_date": three_days_from_now,
                "scheduled_window": "10:00 - 12:00",
                "items": [
                    {"product_key": "Organic Tomatoes::farmer_amit", "quantity": 3},
                    {"product_key": "Fresh Paneer::farmer_amit", "quantity": 1},
                ],
                "delivery": {
                    "driver_name": "Mahesh Pawar",
                    "contact_number": "+91-9012345678",
                    "status": Delivery.Status.SCHEDULED,
                    "assigned_farmer": "farmer_amit",
                },
                "payment": {
                    "provider": Payment.Providers.STRIPE,
                    "status": Payment.Status.SUCCESS,
                    "transaction_id": "STRIPE-TEST-001",
                },
            },
            {
                "customer": "customer_dev",
                "notes": "Sample order 2",
                "status": Order.Status.PENDING,
                "payment_status": Order.PaymentStatus.UNPAID,
                "delivery_address": "Sector 21, Nagpur, Maharashtra",
                "scheduled_date": five_days_from_now,
                "scheduled_window": "14:00 - 16:00",
                "items": [
                    {"product_key": "Alphonso Mangoes::farmer_sunita", "quantity": 2},
                    {"product_key": "Multi-grain Flour::farmer_sunita", "quantity": 1},
                ],
                "delivery": {
                    "driver_name": "Rekha Kulkarni",
                    "contact_number": "+91-9090909090",
                    "status": Delivery.Status.PENDING,
                    "assigned_farmer": "farmer_sunita",
                },
                "payment": None,
            },
            {
                "customer": "customer_riya",
                "notes": "Sample order cart",
                "status": Order.Status.CART,
                "payment_status": Order.PaymentStatus.UNPAID,
                "delivery_address": "Apartment 3B, Mumbai, Maharashtra",
                "scheduled_date": None,
                "scheduled_window": "",
                "items": [
                    {"product_key": "Organic Tomatoes::farmer_amit", "quantity": 1},
                ],
                "delivery": None,
                "payment": None,
            },
        ]

        for spec in order_specs:
            customer_key = spec["customer"]
            customer = self.users.get(customer_key)
            if customer is None:
                raise CommandError(f"Missing user '{customer_key}'. Run user seeding first.")
            order, created = Order.objects.get_or_create(
                customer=customer,
                notes=spec["notes"],
                defaults={
                    "status": spec["status"],
                    "payment_status": spec["payment_status"],
                    "delivery_address": spec["delivery_address"],
                    "scheduled_date": spec["scheduled_date"],
                    "scheduled_window": spec["scheduled_window"],
                },
            )

            if not created:
                changed_fields: list[str] = []
                for field in [
                    "status",
                    "payment_status",
                    "delivery_address",
                    "scheduled_date",
                    "scheduled_window",
                ]:
                    value = spec[field]
                    if getattr(order, field) != value:
                        setattr(order, field, value)
                        changed_fields.append(field)
                if changed_fields:
                    order.save(update_fields=changed_fields)
                self.stdout.write(f"  Order {order.pk} reused.")
            else:
                self.stdout.write(f"  Order {order.pk} created.")

            order.items.all().delete()  # type: ignore[attr-defined]

            for item in spec["items"]:
                product_key = item["product_key"]
                product = self.products.get(product_key)
                if product is None:
                    raise CommandError(
                        f"Missing product '{product_key}'. Run product seeding before orders."
                    )
                OrderItem.objects.create(
                    order=order,
                    product=product,
                    quantity=item["quantity"],
                    price=product.price,
                )

            order.refresh_from_db()

            if spec["delivery"]:
                assigned_farmer_key = spec["delivery"]["assigned_farmer"]
                assigned_farmer = self.users.get(assigned_farmer_key)
                if assigned_farmer is None:
                    raise CommandError(
                        f"Missing user '{assigned_farmer_key}'. Run user seeding first."
                    )
                delivery_defaults = {
                    "driver_name": spec["delivery"]["driver_name"],
                    "contact_number": spec["delivery"]["contact_number"],
                    "status": spec["delivery"]["status"],
                    "assigned_farmer": assigned_farmer,
                }
                Delivery.objects.update_or_create(
                    order=order,
                    defaults=delivery_defaults,
                )

            if spec["payment"]:
                payment_defaults = {
                    "status": spec["payment"]["status"],
                    "amount": order.total_amount,
                    "currency": "INR",
                    "raw_response": {"source": "seed"},
                }
                Payment.objects.update_or_create(
                    order=order,
                    provider=spec["payment"]["provider"],
                    transaction_id=spec["payment"]["transaction_id"],
                    defaults=payment_defaults,
                )

        self.stdout.write("  Orders, deliveries, and payments seeded.")
