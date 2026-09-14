from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q
from apps.products.models import Item, Package
from apps.accounts.models import Address


class Cart(models.Model):
    customer = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="cart",
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )


    @property
    def total_quantity(self):
        return sum(
            cart_item.quantity
            for cart_item in self.cart_items.all()
        )


    @property
    def subtotal(self):
        return sum(
            cart_item.total_price
            for cart_item in self.cart_items.all()
    )


    def __str__(self):
        return f"Cart - {self.customer}"


class CartItem(models.Model):
    cart = models.ForeignKey(
        Cart,
        on_delete=models.CASCADE,
        related_name="cart_items",
    )

    item = models.ForeignKey(
        Item,
        on_delete=models.CASCADE,
        related_name="cart_items",
        null=True,
        blank=True,
    )

    package = models.ForeignKey(
        Package,
        on_delete=models.CASCADE,
        related_name="cart_items",
        null=True,
        blank=True,
    )

    quantity = models.PositiveIntegerField(
        default=1,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=(
                    Q(item__isnull=False, package__isnull=True)
                    | Q(item__isnull=True, package__isnull=False)
                ),
                name="cart_item_must_have_item_or_package",
            ),
        ]

    def clean(self):
        super().clean()

        if self.item and self.package:
            raise ValidationError(
                "A cart item cannot contain both an item and a package."
            )

        if not self.item and not self.package:
            raise ValidationError(
                "A cart item must contain either an item or a package."
            )

    @property
    def product(self):
        return self.item or self.package

    @property
    def unit_price(self):
        return self.product.selling_price

    @property
    def total_price(self):
        return self.unit_price * self.quantity

    def __str__(self):
        product = self.item or self.package

        return f"{product} × {self.quantity}"


class Order(models.Model):

    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending"
        CONFIRMED = "CONFIRMED", "Confirmed"
        PROCESSING = "PROCESSING", "Processing"
        SHIPPED = "SHIPPED", "Shipped"
        DELIVERED = "DELIVERED", "Delivered"
        CANCELLED = "CANCELLED", "Cancelled"

    customer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="orders",
    )

    address = models.ForeignKey(
        Address,
        on_delete=models.PROTECT,
        related_name="orders",
    )

    # Delivery address snapshot
    full_name = models.CharField(
        max_length=150,
        default="",
    )

    phone_number = models.CharField(
        max_length=15,
        default="",
    )

    address_line_1 = models.CharField(
        max_length=255,
        default="",
    )

    address_line_2 = models.CharField(
        max_length=255,
        blank=True,
        default="",
    )

    landmark = models.CharField(
        max_length=255,
        blank=True,
        default="",
    )

    city = models.CharField(
        max_length=100,
        default="",
    )

    state = models.CharField(
        max_length=100,
        default="",
    )

    pincode = models.CharField(
        max_length=10,
        default="",
    )

    country = models.CharField(
        max_length=100,
        default="India",
    )

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
        db_index=True,
    )

    subtotal = models.DecimalField(
        max_digits=12,
        decimal_places=2,
    )

    discount_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
    )

    delivery_charge = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
    )

    total_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        ordering = ["-created_at"]

        indexes = [
            models.Index(
                fields=["customer", "-created_at"],
                name="order_customer_created_idx",
            ),
            models.Index(
                fields=["status", "-created_at"],
                name="order_status_created_idx",
            ),
            models.Index(
                fields=["created_at"],
                name="order_created_at_idx",
            ),
        ]

    def __str__(self):
        return f"Order #{self.id} - {self.customer}"



class Promotion(models.Model):

    class DiscountType(models.TextChoices):
        PERCENTAGE = "PERCENTAGE", "Percentage"
        FIXED = "FIXED", "Fixed Amount"

    code = models.CharField(
        max_length=50,
        unique=True,
        db_index=True,
    )

    discount_type = models.CharField(
        max_length=20,
        choices=DiscountType.choices,
    )

    discount_value = models.DecimalField(
        max_digits=10,
        decimal_places=2,
    )

    minimum_order_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
    )

    maximum_discount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
    )

    start_date = models.DateTimeField()

    end_date = models.DateTimeField()

    usage_limit = models.PositiveIntegerField(
        null=True,
        blank=True,
    )

    per_customer_limit = models.PositiveIntegerField(
        default=1,
    )

    used_count = models.PositiveIntegerField(
        default=0,
    )

    is_active = models.BooleanField(
        default=True,
        db_index=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.code


class PromotionUsage(models.Model):
    promotion = models.ForeignKey(
        Promotion,
        on_delete=models.PROTECT,
        related_name="usages",
    )

    customer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="promotion_usages",
    )

    order = models.OneToOneField(
        Order,
        on_delete=models.PROTECT,
        related_name="promotion_usage",
    )

    discount_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    class Meta:
        ordering = ["-created_at"]

        indexes = [
            models.Index(
                fields=["promotion", "customer"],
                name="promotion_customer_idx",
            ),
            models.Index(
                fields=["customer", "-created_at"],
                name="promotion_usage_customer_idx",
            ),
        ]

    def __str__(self):
        return (
            f"{self.promotion.code} - "
            f"Order #{self.order.id}"
        )


class OrderItem(models.Model):

    class ProductType(models.TextChoices):
        ITEM = "ITEM", "Item"
        PACKAGE = "PACKAGE", "Package"

    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name="order_items",
    )

    item = models.ForeignKey(
        Item,
        on_delete=models.PROTECT,
        related_name="order_items",
        null=True,
        blank=True,
    )

    package = models.ForeignKey(
        Package,
        on_delete=models.PROTECT,
        related_name="order_items",
        null=True,
        blank=True,
    )

    product_type = models.CharField(
        max_length=20,
        choices=ProductType.choices,
    )

    product_name = models.CharField(
        max_length=200,
    )

    product_slug = models.SlugField(
        max_length=220,
    )

    quantity = models.PositiveIntegerField()

    unit_price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
    )

    total_price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    class Meta:
        ordering = ["id"]

        indexes = [
            models.Index(
                fields=["order"],
                name="orderitem_order_idx",
            ),
            models.Index(
                fields=["item"],
                name="orderitem_item_idx",
            ),
            models.Index(
                fields=["package"],
                name="orderitem_package_idx",
            ),
        ]

    def clean(self):
        super().clean()

        if self.item and self.package:
            raise ValidationError(
                "An order item cannot contain both an item and a package."
            )

        if not self.item and not self.package:
            raise ValidationError(
                "An order item must contain either an item or a package."
            )

    def __str__(self):
        return f"{self.product_name} × {self.quantity}"


class OrderStatusHistory(models.Model):

    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name="status_history",
    )

    previous_status = models.CharField(
        max_length=20,
        choices=Order.Status.choices,
    )

    new_status = models.CharField(
        max_length=20,
        choices=Order.Status.choices,
    )

    changed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="order_status_changes",
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    class Meta:
        ordering = ["created_at"]

    def __str__(self):
        return (
            f"Order #{self.order.id}: "
            f"{self.previous_status} → {self.new_status}"
        )


class Payment(models.Model):

    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending"
        SUCCESS = "SUCCESS", "Success"
        FAILED = "FAILED", "Failed"
        REFUNDED = "REFUNDED", "Refunded"

    class Method(models.TextChoices):
        ONLINE = "ONLINE", "Online"
        COD = "COD", "Cash on Delivery"

    order = models.OneToOneField(
        Order,
        on_delete=models.PROTECT,
        related_name="payment",
    )

    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
    )

    method = models.CharField(
        max_length=20,
        choices=Method.choices,
    )

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
        db_index=True,
    )

    transaction_id = models.CharField(
        max_length=200,
        blank=True,
        default="",
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        indexes = [
            models.Index(
                fields=["status", "-created_at"],
                name="payment_status_created_idx",
            ),
            models.Index(
                fields=["method", "-created_at"],
                name="payment_method_created_idx",
            ),
            models.Index(
                fields=["created_at"],
                name="payment_created_at_idx",
            ),
        ]

    def __str__(self):
        return f"Payment - Order #{self.order.id}"


class Refund(models.Model):

    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending"
        SUCCESS = "SUCCESS", "Success"
        FAILED = "FAILED", "Failed"

    payment = models.ForeignKey(
        Payment,
        on_delete=models.PROTECT,
        related_name="refunds",
    )

    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
    )

    reason = models.CharField(
        max_length=255,
        blank=True,
        default="",
    )

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
        db_index=True,
    )

    refund_reference = models.CharField(
        max_length=200,
        blank=True,
        default="",
    )

    processed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="processed_refunds",
        null=True,
        blank=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=Q(amount__gt=0),
                name="refund_amount_positive",
            ),
        ]

        indexes = [
            models.Index(
                fields=["payment", "status"],
                name="refund_payment_status_idx",
            ),
            models.Index(
                fields=["created_at"],
                name="refund_created_at_idx",
            ),
        ]

    def __str__(self):
        return (
            f"Refund - Payment #{self.payment.id}"
        )


class Review(models.Model):

    item = models.ForeignKey(
        "products.Item",
        on_delete=models.CASCADE,
        related_name="reviews",
        null=True,
        blank=True,
    )

    package = models.ForeignKey(
        "products.Package",
        on_delete=models.CASCADE,
        related_name="reviews",
        null=True,
        blank=True,
    )

    customer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="reviews",
    )

    rating = models.PositiveSmallIntegerField()

    review = models.TextField(
        blank=True,
    )

    is_approved = models.BooleanField(
        default=False,
        db_index=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        ordering = ["-created_at"]

        constraints = [
            models.CheckConstraint(
                condition=(
                    models.Q(item__isnull=False)
                    | models.Q(package__isnull=False)
                ),
                name="review_has_product",
            ),
            models.CheckConstraint(
                condition=(
                    models.Q(item__isnull=True)
                    | models.Q(package__isnull=True)
                ),
                name="review_only_one_product",
            ),
            models.CheckConstraint(
                condition=models.Q(rating__gte=1, rating__lte=5),
                name="review_rating_1_to_5",
            ),
            models.UniqueConstraint(
                fields=["customer", "item"],
                condition=models.Q(item__isnull=False),
                name="unique_customer_item_review",
            ),
            models.UniqueConstraint(
                fields=["customer", "package"],
                condition=models.Q(package__isnull=False),
                name="unique_customer_package_review",
            ),
        ]

    def __str__(self):
        product_name = self.item or self.package

        return (
            f"{self.customer} - "
            f"{product_name} - "
            f"{self.rating}"
        )