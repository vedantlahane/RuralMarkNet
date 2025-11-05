"""Tests for order creation views."""
from __future__ import annotations

from decimal import Decimal

from django.test import TestCase
from django.urls import reverse

from accounts.models import AuditLog, User
from orders.models import Order, OrderItem
from products.models import Product


class CartViewTests(TestCase):
    """Ensure cart operations behave."""

    def setUp(self) -> None:
        self.customer = User.objects.create_user(
            username="customer",
            password="pass1234",
            role=User.Roles.CUSTOMER,
        )
        farmer = User.objects.create_user(
            username="farmer",
            password="pass1234",
            role=User.Roles.FARMER,
        )
        self.product = Product.objects.create(
            name="Apple",
            category=Product.Categories.FRUITS,
            price=Decimal("5.00"),
            inventory=10,
            farmer=farmer,
        )

    def test_add_to_cart_requires_login(self) -> None:
        response = self.client.post(reverse("orders:add-to-cart", args=[self.product.pk]))
        self.assertEqual(response.status_code, 302)

    def test_customer_can_add_to_cart(self) -> None:
        self.client.login(username="customer", password="pass1234")
        self.client.post(reverse("orders:add-to-cart", args=[self.product.pk]))
        order = Order.objects.get(customer=self.customer)
        self.assertEqual(OrderItem.objects.filter(order=order).count(), 1)

    def test_customer_can_choose_quantity(self) -> None:
        self.client.login(username="customer", password="pass1234")
        self.client.post(
            reverse("orders:add-to-cart", args=[self.product.pk]),
            data={"quantity": 3},
        )
        order = Order.objects.get(customer=self.customer)
        item = OrderItem.objects.get(order=order, product=self.product)
        self.assertEqual(item.quantity, 3)

    def test_subsequent_adds_increment_existing_item(self) -> None:
        self.client.login(username="customer", password="pass1234")
        self.client.post(
            reverse("orders:add-to-cart", args=[self.product.pk]),
            data={"quantity": 2},
        )
        self.client.post(
            reverse("orders:add-to-cart", args=[self.product.pk]),
            data={"quantity": 3},
        )
        order = Order.objects.get(customer=self.customer)
        item = OrderItem.objects.get(order=order, product=self.product)
        self.assertEqual(item.quantity, 5)

    def test_quantity_is_capped_by_inventory(self) -> None:
        self.product.inventory = 4
        self.product.save(update_fields=["inventory"])

        self.client.login(username="customer", password="pass1234")
        self.client.post(
            reverse("orders:add-to-cart", args=[self.product.pk]),
            data={"quantity": 10},
        )

        order = Order.objects.get(customer=self.customer)
        item = OrderItem.objects.get(order=order, product=self.product)
        self.assertEqual(item.quantity, 4)


class OrderViewTests(TestCase):
    """Customer-facing order detail and cancellation behaviour."""

    def setUp(self) -> None:
        self.customer = User.objects.create_user(
            username="buyer",
            password="pass1234",
            role=User.Roles.CUSTOMER,
        )
        self.client.login(username="buyer", password="pass1234")

        self.farmer = User.objects.create_user(
            username="farmer",
            password="pass1234",
            role=User.Roles.FARMER,
        )
        self.product = Product.objects.create(
            name="Banana",
            category=Product.Categories.FRUITS,
            price=Decimal("12.00"),
            inventory=20,
            farmer=self.farmer,
        )

    def _create_order(self, status: str = Order.Status.PENDING) -> Order:
        order = Order.objects.create(customer=self.customer, status=status)
        OrderItem.objects.create(
            order=order,
            product=self.product,
            quantity=2,
            price=self.product.price,
        )
        return order

    def test_order_detail_displays_items(self) -> None:
        order = self._create_order()
        response = self.client.get(reverse("orders:detail", args=[order.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.product.name)
        self.assertContains(response, "Cancel order")

    def test_customer_can_cancel_pending_order(self) -> None:
        order = self._create_order()
        response = self.client.post(reverse("orders:cancel", args=[order.pk]), follow=True)
        self.assertRedirects(response, reverse("orders:list"))
        order.refresh_from_db()
        self.assertEqual(order.status, Order.Status.CANCELLED)
        self.assertTrue(
            AuditLog.objects.filter(
                object_id=str(order.pk), action__icontains="cancelled"
            ).exists()
        )

    def test_shipping_stage_blocks_cancellation(self) -> None:
        order = self._create_order(status=Order.Status.SHIPPED)
        response = self.client.post(reverse("orders:cancel", args=[order.pk]), follow=True)
        order.refresh_from_db()
        self.assertEqual(order.status, Order.Status.SHIPPED)
        self.assertContains(response, "Shipped orders require support assistance")
