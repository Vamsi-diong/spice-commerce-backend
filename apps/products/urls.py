from django.urls import path

from .views import (
    CollectionListAPIView,
    CollectionDetailAPIView,
    CategoryListAPIView,
    CategoryDetailAPIView,
    ItemListAPIView,
    ItemDetailAPIView,
    PackageListAPIView,
    PackageDetailAPIView,
)


urlpatterns = [

    path("collections/",CollectionListAPIView.as_view(),name="collection-list",),
    path("collections/<slug:slug>/",CollectionDetailAPIView.as_view(),name="collection-detail",),
    path("categories/",CategoryListAPIView.as_view(),name="category-list",),
    path("categories/<slug:slug>/",CategoryDetailAPIView.as_view(),name="category-detail",),
    path("items/",ItemListAPIView.as_view(),name="item-list",),
    path("items/<slug:slug>/",ItemDetailAPIView.as_view(),name="item-detail",),
    path("packages/",PackageListAPIView.as_view(),name="package-list",),
    path("packages/<slug:slug>/",PackageDetailAPIView.as_view(),name="package-detail",),
    
]