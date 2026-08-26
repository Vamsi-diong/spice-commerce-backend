from django.contrib import admin

from .models import (
    Collection,
    Category,
    Item,
    Package,
    PackageItem
)


@admin.register(Collection)
class CollectionAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "slug",
        "is_active",
        "created_at",
    )

    list_filter = (
        "is_active",
    )

    search_fields = (
        "name",
        "slug",
    )

    ordering = (
        "name",
    )

    prepopulated_fields = {
        "slug": ("name",),
    }


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "collection",
        "slug",
        "is_active",
        "created_at",
    )

    list_filter = (
        "collection",
        "is_active",
    )

    search_fields = (
        "name",
        "slug",
        "collection__name",
    )

    ordering = (
        "collection__name",
        "name",
    )

    prepopulated_fields = {
        "slug": ("name",),
    }


@admin.register(Item)
class ItemAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "sku",
        "category",
        "get_collection",
        "weight",
        "unit",
        "mrp",
        "selling_price",
        "stock_quantity",
        "is_active",
        "is_featured",
    )

    list_filter = (
        "is_active",
        "is_featured",
        "category",
        "category__collection",
    )

    search_fields = (
        "name",
        "slug",
        "sku",
        "category__name",
        "category__collection__name",
    )

    ordering = (
        "name",
    )

    prepopulated_fields = {
        "slug": ("name",),
    }

    readonly_fields = (
        "created_at",
        "updated_at",
    )

    fieldsets = (
        (
            "Basic Information",
            {
                "fields": (
                    "category",
                    "name",
                    "slug",
                    "sku",
                    "short_description",
                    "description",
                    "ingredients",
                )
            },
        ),
        (
            "Package Details",
            {
                "fields": (
                    "weight",
                    "unit",
                )
            },
        ),
        (
            "Pricing",
            {
                "fields": (
                    "mrp",
                    "selling_price",
                )
            },
        ),
        (
            "Inventory",
            {
                "fields": (
                    "stock_quantity",
                    "low_stock_threshold",
                )
            },
        ),
        (
            "Status",
            {
                "fields": (
                    "is_active",
                    "is_featured",
                )
            },
        ),
        (
            "System Information",
            {
                "fields": (
                    "created_at",
                    "updated_at",
                )
            },
        ),
    )

    @admin.display(
        description="Collection",
        ordering="category__collection__name",
    )
    def get_collection(self, obj):
        return obj.category.collection.name


class PackageItemInline(admin.TabularInline):
    model = PackageItem
    extra = 1
    min_num = 1
    autocomplete_fields = ("item",)


@admin.register(Package)
class PackageAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "mrp",
        "selling_price",
        "is_active",
        "is_featured",
        "created_at",
    )

    list_filter = (
        "is_active",
        "is_featured",
    )

    search_fields = (
        "name",
        "slug",
    )

    ordering = (
        "name",
    )

    prepopulated_fields = {
        "slug": ("name",),
    }

    readonly_fields = (
        "created_at",
        "updated_at",
    )

    inlines = (
        PackageItemInline,
    )

    fieldsets = (
        (
            "Package Information",
            {
                "fields": (
                    "name",
                    "slug",
                    "short_description",
                    "description",
                )
            },
        ),
        (
            "Pricing",
            {
                "fields": (
                    "mrp",
                    "selling_price",
                )
            },
        ),
        (
            "Status",
            {
                "fields": (
                    "is_active",
                    "is_featured",
                )
            },
        ),
        (
            "System Information",
            {
                "fields": (
                    "created_at",
                    "updated_at",
                )
            },
        ),
    )


@admin.register(PackageItem)
class PackageItemAdmin(admin.ModelAdmin):
    list_display = (
        "package",
        "item",
        "quantity",
    )

    list_filter = (
        "package",
    )

    search_fields = (
        "package__name",
        "item__name",
        "item__sku",
    )

    autocomplete_fields = (
        "package",
        "item",
    )