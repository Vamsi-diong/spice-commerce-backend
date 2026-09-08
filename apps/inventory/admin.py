from django.contrib import admin

from .models import (
    Cart,
    CartItem,
    Order,
    OrderItem,
    OrderStatusHistory,
    Payment,
    Refund,
)


# =========================================================
# CART
# =========================================================

class CartItemInline(admin.TabularInline):
    model = CartItem
    extra = 0

    readonly_fields = (
        "created_at",
        "updated_at",
    )


@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):

    list_display = (
        "id",
        "customer",
        "get_total_items",
        "created_at",
        "updated_at",
    )

    search_fields = (
        "customer__phone_number",
        "customer__email",
        "customer__first_name",
        "customer__last_name",
    )

    readonly_fields = (
        "created_at",
        "updated_at",
    )

    inlines = (
        CartItemInline,
    )

    @admin.display(description="Total Items")
    def get_total_items(self, obj):
        return sum(
            cart_item.quantity
            for cart_item in obj.cart_items.all()
        )


@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):

    list_display = (
        "id",
        "cart",
        "item",
        "package",
        "quantity",
        "created_at",
        "updated_at",
    )

    list_filter = (
        "created_at",
    )

    search_fields = (
        "item__name",
        "package__name",
        "cart__customer__phone_number",
        "cart__customer__email",
    )

    readonly_fields = (
        "created_at",
        "updated_at",
    )


# =========================================================
# ORDER
# =========================================================

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0

    readonly_fields = (
        "product_type",
        "product_name",
        "product_slug",
        "quantity",
        "unit_price",
        "total_price",
        "created_at",
    )


class OrderStatusHistoryInline(admin.TabularInline):
    model = OrderStatusHistory
    extra = 0

    readonly_fields = (
        "previous_status",
        "new_status",
        "changed_by",
        "created_at",
    )


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):

    list_display = (
        "id",
        "customer",
        "status",
        "subtotal",
        "delivery_charge",
        "total_amount",
        "created_at",
        "updated_at",
    )

    list_filter = (
        "status",
        "created_at",
        "updated_at",
    )

    search_fields = (
        "id",
        "customer__phone_number",
        "customer__email",
        "customer__first_name",
        "customer__last_name",
        "full_name",
        "phone_number",
        "city",
        "pincode",
    )

    readonly_fields = (
        "created_at",
        "updated_at",
    )

    fieldsets = (
        (
            "Order Information",
            {
                "fields": (
                    "customer",
                    "address",
                    "status",
                )
            },
        ),
        (
            "Delivery Address Snapshot",
            {
                "fields": (
                    "full_name",
                    "phone_number",
                    "address_line_1",
                    "address_line_2",
                    "landmark",
                    "city",
                    "state",
                    "pincode",
                    "country",
                )
            },
        ),
        (
            "Amount",
            {
                "fields": (
                    "subtotal",
                    "delivery_charge",
                    "total_amount",
                )
            },
        ),
        (
            "Timestamps",
            {
                "fields": (
                    "created_at",
                    "updated_at",
                )
            },
        ),
    )

    inlines = (
        OrderItemInline,
        OrderStatusHistoryInline,
    )


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):

    list_display = (
        "id",
        "order",
        "product_type",
        "product_name",
        "quantity",
        "unit_price",
        "total_price",
        "created_at",
    )

    list_filter = (
        "product_type",
        "created_at",
    )

    search_fields = (
        "product_name",
        "product_slug",
        "order__id",
        "order__customer__phone_number",
        "order__customer__email",
    )

    readonly_fields = (
        "created_at",
    )


@admin.register(OrderStatusHistory)
class OrderStatusHistoryAdmin(admin.ModelAdmin):

    list_display = (
        "id",
        "order",
        "previous_status",
        "new_status",
        "changed_by",
        "created_at",
    )

    list_filter = (
        "previous_status",
        "new_status",
        "created_at",
    )

    search_fields = (
        "order__id",
        "changed_by__phone_number",
        "changed_by__email",
        "changed_by__first_name",
        "changed_by__last_name",
    )

    readonly_fields = (
        "created_at",
    )


# =========================================================
# PAYMENT
# =========================================================

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):

    list_display = (
        "id",
        "order",
        "get_customer",
        "amount",
        "method",
        "status",
        "transaction_id",
        "created_at",
        "updated_at",
    )

    list_filter = (
        "method",
        "status",
        "created_at",
        "updated_at",
    )

    search_fields = (
        "id",
        "order__id",
        "order__customer__phone_number",
        "order__customer__email",
        "order__customer__first_name",
        "order__customer__last_name",
        "transaction_id",
    )

    readonly_fields = (
        "created_at",
        "updated_at",
    )

    @admin.display(description="Customer")
    def get_customer(self, obj):
        customer = obj.order.customer

        full_name = (
            f"{customer.first_name} "
            f"{customer.last_name}"
        ).strip()

        return (
            full_name
            or customer.phone_number
        )


# =========================================================
# REFUND
# =========================================================

@admin.register(Refund)
class RefundAdmin(admin.ModelAdmin):

    list_display = (
        "id",
        "payment",
        "get_order",
        "get_customer",
        "amount",
        "status",
        "refund_reference",
        "processed_by",
        "created_at",
        "updated_at",
    )

    list_filter = (
        "status",
        "created_at",
        "updated_at",
    )

    search_fields = (
        "id",
        "payment__id",
        "payment__order__id",
        "payment__order__customer__phone_number",
        "payment__order__customer__email",
        "refund_reference",
        "reason",
    )

    readonly_fields = (
        "created_at",
        "updated_at",
    )

    @admin.display(description="Order")
    def get_order(self, obj):
        return obj.payment.order.id

    @admin.display(description="Customer")
    def get_customer(self, obj):
        customer = obj.payment.order.customer

        full_name = (
            f"{customer.first_name} "
            f"{customer.last_name}"
        ).strip()

        return (
            full_name
            or customer.phone_number
        )