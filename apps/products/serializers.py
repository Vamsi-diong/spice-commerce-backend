from rest_framework import serializers

from .models import (
    Collection,
    Category,
    Item,
    Package,
    PackageItem,
)


class CollectionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Collection
        fields = (
            "id",
            "name",
            "slug",
            "description",
        )


class CategorySerializer(serializers.ModelSerializer):
    collection = CollectionSerializer(
        read_only=True,
    )

    class Meta:
        model = Category
        fields = (
            "id",
            "name",
            "slug",
            "description",
            "collection",
        )


class ItemListSerializer(serializers.ModelSerializer):
    collection = serializers.CharField(
        source="category.collection.name",
        read_only=True,
    )

    collection_slug = serializers.CharField(
        source="category.collection.slug",
        read_only=True,
    )

    category = serializers.CharField(
        source="category.name",
        read_only=True,
    )

    category_slug = serializers.CharField(
        source="category.slug",
        read_only=True,
    )

    class Meta:
        model = Item
        fields = (
            "id",
            "name",
            "slug",
            "short_description",
            "weight",
            "unit",
            "mrp",
            "selling_price",
            "in_stock",
            "is_low_stock",
            "is_featured",
            "collection",
            "collection_slug",
            "category",
            "category_slug",
        )


class ItemDetailSerializer(serializers.ModelSerializer):
    collection = serializers.CharField(
        source="category.collection.name",
        read_only=True,
    )

    collection_slug = serializers.CharField(
        source="category.collection.slug",
        read_only=True,
    )

    category = serializers.CharField(
        source="category.name",
        read_only=True,
    )

    category_slug = serializers.CharField(
        source="category.slug",
        read_only=True,
    )

    class Meta:
        model = Item
        fields = (
            "id",
            "name",
            "slug",
            "short_description",
            "description",
            "ingredients",
            "weight",
            "unit",
            "mrp",
            "selling_price",
            "in_stock",
            "is_low_stock",
            "is_featured",
            "collection",
            "collection_slug",
            "category",
            "category_slug",
        )


class PackageItemSerializer(serializers.ModelSerializer):
    item = ItemListSerializer(
        read_only=True,
    )

    class Meta:
        model = PackageItem
        fields = (
            "id",
            "item",
            "quantity",
        )


class PackageListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Package
        fields = (
            "id",
            "name",
            "slug",
            "available_quantity",
            "in_stock",
            "short_description",
            "mrp",
            "selling_price",
            "is_featured",
        )


class PackageDetailSerializer(serializers.ModelSerializer):
    package_items = PackageItemSerializer(
        many=True,
        read_only=True,
    )

    class Meta:
        model = Package
        fields = (
            "id",
            "name",
            "slug",
            "available_quantity",
            "in_stock",
            "short_description",
            "description",
            "mrp",
            "selling_price",
            "is_featured",
            "package_items",
        )