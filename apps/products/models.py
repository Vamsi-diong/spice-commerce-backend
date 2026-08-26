from django.db import models
from django.core.exceptions import ValidationError

# Create your models here.

class Collection(models.Model):
    name = models.CharField(
        max_length=100,
        unique=True,
    )

    slug = models.SlugField(
        max_length=120,
        unique=True,
    )

    description = models.TextField(
        blank=True,
    )

    is_active = models.BooleanField(
        default=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class Category(models.Model):
    collection = models.ForeignKey(
        Collection,
        on_delete=models.CASCADE,
        related_name="categories",
    )

    name = models.CharField(
        max_length=100,
    )

    slug = models.SlugField(
        max_length=120,
    )

    description = models.TextField(
        blank=True,
    )

    is_active = models.BooleanField(
        default=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        ordering = ["collection__name", "name"]

        constraints = [
            models.UniqueConstraint(
                fields=["collection", "name"],
                name="unique_category_per_collection",
            ),
            models.UniqueConstraint(
                fields=["collection", "slug"],
                name="unique_category_slug_per_collection",
            ),
        ]

    def __str__(self):
        return f"{self.collection.name} - {self.name}"


class Item(models.Model):
    category = models.ForeignKey(
        Category,
        on_delete=models.PROTECT,
        related_name="items",
    )

    name = models.CharField(
        max_length=200,
    )

    slug = models.SlugField(
        max_length=220,
        unique=True,
    )

    sku = models.CharField(
        max_length=100,
        unique=True,
    )

    short_description = models.CharField(
        max_length=500,
        blank=True,
    )

    description = models.TextField(
        blank=True,
    )

    ingredients = models.TextField(
        blank=True,
    )

    weight = models.DecimalField(
        max_digits=10,
        decimal_places=2,
    )

    unit = models.CharField(
        max_length=20,
        default="g",
    )

    mrp = models.DecimalField(
        max_digits=10,
        decimal_places=2,
    )

    selling_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
    )

    stock_quantity = models.PositiveIntegerField(
        default=0,
    )

    low_stock_threshold = models.PositiveIntegerField(
        default=5,
    )

    is_active = models.BooleanField(
        default=True,
    )

    is_featured = models.BooleanField(
        default=False,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        ordering = ["name"]

    def clean(self):
        super().clean()

        if (
            self.mrp is not None
            and self.selling_price is not None
            and self.selling_price > self.mrp
        ):
            raise ValidationError(
                {
                    "selling_price": (
                        "Selling price cannot be greater than MRP."
                    )
                }
            )

    def __str__(self):
        return f"{self.name} - {self.weight}{self.unit}"

    @property
    def in_stock(self):
        return self.stock_quantity > 0

    @property
    def is_low_stock(self):
        return (
            self.stock_quantity > 0
            and self.stock_quantity <= self.low_stock_threshold
        )


class Package(models.Model):
    name = models.CharField(
        max_length=200,
    )

    slug = models.SlugField(
        max_length=220,
        unique=True,
    )

    short_description = models.CharField(
        max_length=500,
        blank=True,
    )

    description = models.TextField(
        blank=True,
    )

    mrp = models.DecimalField(
        max_digits=10,
        decimal_places=2,
    )

    selling_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
    )

    is_active = models.BooleanField(
        default=True,
    )

    is_featured = models.BooleanField(
        default=False,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        ordering = ["name"]

    def clean(self):
        super().clean()

        if self.selling_price > self.mrp:
            raise ValidationError(
                {
                    "selling_price": (
                        "Selling price cannot be greater than MRP."
                    )
                }
            )

    def __str__(self):
        return self.name

    @property
    def available_quantity(self):
        package_items = self.package_items.select_related("item").all()

        if not package_items.exists():
            return 0

        available_quantities = []

        for package_item in package_items:
            available_quantity = (
                package_item.item.stock_quantity // package_item.quantity
            )

            available_quantities.append(available_quantity)

        return min(available_quantities)


    @property
    def in_stock(self):
        return self.available_quantity > 0


class PackageItem(models.Model):
    package = models.ForeignKey(
        Package,
        on_delete=models.CASCADE,
        related_name="package_items",
    )

    item = models.ForeignKey(
        Item,
        on_delete=models.PROTECT,
        related_name="package_entries",
    )

    quantity = models.PositiveIntegerField(
        default=1,
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["package", "item"],
                name="unique_item_per_package",
            ),
        ]

    def __str__(self):
        return f"{self.package.name} - {self.item.name}"