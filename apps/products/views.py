from django.shortcuts import render

# Create your views here.
from rest_framework import generics
from rest_framework.filters import SearchFilter
from .pagination import StandardResultsSetPagination

from .models import (
    Collection,
    Category,
    Item,
    Package,
)
from .serializers import (
    CollectionSerializer,
    CategorySerializer,
    ItemListSerializer,
    ItemDetailSerializer,
    PackageListSerializer,
    PackageDetailSerializer,
)


class CollectionListAPIView(generics.ListAPIView):
    serializer_class = CollectionSerializer

    def get_queryset(self):
        return Collection.objects.filter(
            is_active=True,
        )


class CollectionDetailAPIView(generics.RetrieveAPIView):
    serializer_class = CollectionSerializer
    lookup_field = "slug"

    def get_queryset(self):
        return Collection.objects.filter(
            is_active=True,
        )


class CategoryListAPIView(generics.ListAPIView):
    serializer_class = CategorySerializer

    def get_queryset(self):
        queryset = Category.objects.filter(
            is_active=True,
            collection__is_active=True,
        )

        collection_slug = self.request.query_params.get("collection")

        if collection_slug:
            queryset = queryset.filter(
                collection__slug=collection_slug,
            )

        return queryset


class CategoryDetailAPIView(generics.RetrieveAPIView):
    serializer_class = CategorySerializer
    lookup_field = "slug"

    def get_queryset(self):
        return Category.objects.filter(
            is_active=True,
            collection__is_active=True,
        )


class ItemListAPIView(generics.ListAPIView):
    serializer_class = ItemListSerializer
    filter_backends = (
        SearchFilter,
    )
    pagination_class = StandardResultsSetPagination

    search_fields = (
        "name",
        "short_description",
        "category__name",
    )

    def get_queryset(self):
        queryset = Item.objects.filter(
            is_active=True,
            category__is_active=True,
            category__collection__is_active=True,
        ).select_related(
            "category",
            "category__collection",
        )

        # Collection filter
        collection_slug = self.request.query_params.get("collection")

        if collection_slug:
            queryset = queryset.filter(
                category__collection__slug=collection_slug,
            )

        # Category filter
        category_slug = self.request.query_params.get("category")

        if category_slug:
            queryset = queryset.filter(
                category__slug=category_slug,
            )

        # Featured filter
        featured = self.request.query_params.get("featured")

        if featured is not None:
            featured_value = featured.lower()

            if featured_value == "true":
                queryset = queryset.filter(
                    is_featured=True,
                )

            elif featured_value == "false":
                queryset = queryset.filter(
                    is_featured=False,
                )

        # Minimum price filter
        min_price = self.request.query_params.get("min_price")

        if min_price:
            queryset = queryset.filter(
                selling_price__gte=min_price,
            )

        # Maximum price filter
        max_price = self.request.query_params.get("max_price")

        if max_price:
            queryset = queryset.filter(
                selling_price__lte=max_price,
            )

        # Ordering
        ordering = self.request.query_params.get("ordering")

        ordering_map = {
            "price_low_to_high": "selling_price",
            "price_high_to_low": "-selling_price",
            "name_a_to_z": "name",
            "name_z_to_a": "-name",
            "newest": "-created_at",
            "oldest": "created_at",
        }

        if ordering in ordering_map:
            queryset = queryset.order_by(
                ordering_map[ordering],
            )

        return queryset


class ItemDetailAPIView(generics.RetrieveAPIView):
    serializer_class = ItemDetailSerializer
    lookup_field = "slug"

    def get_queryset(self):
        return Item.objects.filter(
            is_active=True,
            category__is_active=True,
            category__collection__is_active=True,
        ).select_related(
            "category",
            "category__collection",
        )


class PackageListAPIView(generics.ListAPIView):
    serializer_class = PackageListSerializer
    filter_backends = (
        SearchFilter,
    )
    pagination_class = StandardResultsSetPagination

    search_fields = (
        "name",
        "short_description",
    )

    def get_queryset(self):
        queryset = Package.objects.filter(
            is_active=True,
        ).prefetch_related(
            "package_items__item",
        )

        # Featured filter
        featured = self.request.query_params.get("featured")

        if featured is not None:
            featured_value = featured.lower()

            if featured_value == "true":
                queryset = queryset.filter(
                    is_featured=True,
                )

            elif featured_value == "false":
                queryset = queryset.filter(
                    is_featured=False,
                )

        # Minimum price filter
        min_price = self.request.query_params.get("min_price")

        if min_price:
            queryset = queryset.filter(
                selling_price__gte=min_price,
            )

        # Maximum price filter
        max_price = self.request.query_params.get("max_price")

        if max_price:
            queryset = queryset.filter(
                selling_price__lte=max_price,
            )

        # Ordering
        ordering = self.request.query_params.get("ordering")

        ordering_map = {
            "price_low_to_high": "selling_price",
            "price_high_to_low": "-selling_price",
            "name_a_to_z": "name",
            "name_z_to_a": "-name",
            "newest": "-created_at",
            "oldest": "created_at",
        }

        if ordering in ordering_map:
            queryset = queryset.order_by(
                ordering_map[ordering],
            )

        return queryset


class PackageDetailAPIView(generics.RetrieveAPIView):
    serializer_class = PackageDetailSerializer
    lookup_field = "slug"

    def get_queryset(self):
        return Package.objects.filter(
            is_active=True,
        ).prefetch_related(
            "package_items__item__category__collection",
        )