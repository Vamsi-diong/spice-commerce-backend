from django.contrib import admin

# Register your models here.
from .models import User,Address


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = (
        "email",
        "first_name",
        "last_name",
        "role",
        "is_verified",
        "is_active",
        "is_staff",
        "date_joined",
    )

    list_filter = (
        "role",
        "is_verified",
        "is_active",
        "is_staff",
    )

    search_fields = (
        "email",
        "phone_number",
        "first_name",
        "last_name",
    )

    ordering = ("-date_joined",)


@admin.register(Address)
class AddressAdmin(admin.ModelAdmin):
    list_display = (
        "full_name",
        "user",
        "address_type",
        "city",
        "state",
        "pincode",
        "is_default",
    )

    list_filter = (
        "address_type",
        "state",
        "city",
        "is_default",
    )

    search_fields = (
        "full_name",
        "phone_number",
        "city",
        "state",
        "pincode",
        "user__email",
    )

    ordering = ("-created_at",)