from rest_framework import serializers
from .models import Cart, CartItem,Order, OrderItem, Payment,OrderStatusHistory,Refund,Promotion, Review


class CartItemSerializer(serializers.ModelSerializer):
    product_type = serializers.SerializerMethodField()
    product_id = serializers.SerializerMethodField()
    product_name = serializers.SerializerMethodField()
    product_slug = serializers.SerializerMethodField()

    unit_price = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
        read_only=True,
    )

    total_price = serializers.DecimalField(
        max_digits=12,
        decimal_places=2,
        read_only=True,
    )

    class Meta:
        model = CartItem

        fields = (
            "id",
            "product_type",
            "product_id",
            "product_name",
            "product_slug",
            "quantity",
            "unit_price",
            "total_price",
            "created_at",
            "updated_at",
        )

    def get_product_type(self, obj):
        if obj.item:
            return "item"

        return "package"

    def get_product_id(self, obj):
        return obj.product.id

    def get_product_name(self, obj):
        return obj.product.name

    def get_product_slug(self, obj):
        return obj.product.slug


class CartSerializer(serializers.ModelSerializer):
    cart_items = CartItemSerializer(
        many=True,
        read_only=True,
    )

    total_quantity = serializers.IntegerField(
        read_only=True,
    )

    subtotal = serializers.DecimalField(
        max_digits=12,
        decimal_places=2,
        read_only=True,
    )

    class Meta:
        model = Cart

        fields = (
            "id",
            "cart_items",
            "total_quantity",
            "subtotal",
            "created_at",
            "updated_at",
        )


class AddCartItemSerializer(serializers.Serializer):
    item_id = serializers.IntegerField(
        required=False,
    )

    package_id = serializers.IntegerField(
        required=False,
    )

    quantity = serializers.IntegerField(
        min_value=1,
        default=1,
    )

    def validate(self, attrs):
        item_id = attrs.get("item_id")
        package_id = attrs.get("package_id")

        if item_id and package_id:
            raise serializers.ValidationError(
                "Provide either item_id or package_id, not both."
            )

        if not item_id and not package_id:
            raise serializers.ValidationError(
                "You must provide either item_id or package_id."
            )

        return attrs

class UpdateCartItemSerializer(serializers.Serializer):
    quantity = serializers.IntegerField(
        min_value=1,
    )


class CheckoutSerializer(serializers.Serializer):
    address_id = serializers.IntegerField(
        min_value=1,
    )

    promotion_code = serializers.CharField(
        max_length=50,
        required=False,
        allow_blank=True,
        trim_whitespace=True,
    )


class PromotionSerializer(serializers.ModelSerializer):

    class Meta:
        model = Promotion

        fields = (
            "id",
            "code",
            "discount_type",
            "discount_value",
            "minimum_order_amount",
            "maximum_discount",
            "start_date",
            "end_date",
            "usage_limit",
            "per_customer_limit",
            "used_count",
            "is_active",
            "created_at",
            "updated_at",
        )

        read_only_fields = (
            "id",
            "used_count",
            "created_at",
            "updated_at",
        )

    def validate_code(self, value):
        return value.strip().upper()

    def validate(self, attrs):

        discount_type = attrs.get(
            "discount_type",
            getattr(
                self.instance,
                "discount_type",
                None,
            ),
        )

        discount_value = attrs.get(
            "discount_value",
            getattr(
                self.instance,
                "discount_value",
                None,
            ),
        )

        minimum_order_amount = attrs.get(
            "minimum_order_amount",
            getattr(
                self.instance,
                "minimum_order_amount",
                0,
            ),
        )

        maximum_discount = attrs.get(
            "maximum_discount",
            getattr(
                self.instance,
                "maximum_discount",
                None,
            ),
        )

        start_date = attrs.get(
            "start_date",
            getattr(
                self.instance,
                "start_date",
                None,
            ),
        )

        end_date = attrs.get(
            "end_date",
            getattr(
                self.instance,
                "end_date",
                None,
            ),
        )

        usage_limit = attrs.get(
            "usage_limit",
            getattr(
                self.instance,
                "usage_limit",
                None,
            ),
        )

        per_customer_limit = attrs.get(
            "per_customer_limit",
            getattr(
                self.instance,
                "per_customer_limit",
                1,
            ),
        )

        if discount_value is not None and discount_value <= 0:
            raise serializers.ValidationError(
                {
                    "discount_value": (
                        "Discount value must be greater than 0."
                    )
                }
            )

        if (
            minimum_order_amount is not None
            and minimum_order_amount < 0
        ):
            raise serializers.ValidationError(
                {
                    "minimum_order_amount": (
                        "Minimum order amount cannot be negative."
                    )
                }
            )

        if (
            maximum_discount is not None
            and maximum_discount <= 0
        ):
            raise serializers.ValidationError(
                {
                    "maximum_discount": (
                        "Maximum discount must be greater than 0."
                    )
                }
            )

        if (
            discount_type == Promotion.DiscountType.PERCENTAGE
            and discount_value is not None
            and discount_value > 100
        ):
            raise serializers.ValidationError(
                {
                    "discount_value": (
                        "Percentage discount cannot exceed 100."
                    )
                }
            )

        if (
            start_date
            and end_date
            and end_date <= start_date
        ):
            raise serializers.ValidationError(
                {
                    "end_date": (
                        "End date must be after start date."
                    )
                }
            )

        if usage_limit is not None and usage_limit < 1:
            raise serializers.ValidationError(
                {
                    "usage_limit": (
                        "Usage limit must be at least 1."
                    )
                }
            )

        if (
            per_customer_limit is not None
            and per_customer_limit < 1
        ):
            raise serializers.ValidationError(
                {
                    "per_customer_limit": (
                        "Per-customer limit must be at least 1."
                    )
                }
            )


        return attrs


class ReviewSerializer(serializers.ModelSerializer):

    item_id = serializers.IntegerField(
        write_only=True,
        required=False,
        min_value=1,
    )

    package_id = serializers.IntegerField(
        write_only=True,
        required=False,
        min_value=1,
    )

    product_type = serializers.SerializerMethodField()

    product_id = serializers.SerializerMethodField()

    product_name = serializers.SerializerMethodField()

    customer_name = serializers.SerializerMethodField()

    class Meta:
        model = Review

        fields = (
            "id",
            "item_id",
            "package_id",
            "product_type",
            "product_id",
            "product_name",
            "customer_name",
            "rating",
            "review",
            "is_approved",
            "created_at",
            "updated_at",
        )

        read_only_fields = (
            "id",
            "product_type",
            "product_id",
            "product_name",
            "customer_name",
            "is_approved",
            "created_at",
            "updated_at",
        )

    def validate(self, attrs):

        item_id = attrs.get("item_id")
        package_id = attrs.get("package_id")

        if item_id and package_id:
            raise serializers.ValidationError(
                "Provide either item_id or package_id, not both."
            )

        if not item_id and not package_id:
            raise serializers.ValidationError(
                "You must provide either item_id or package_id."
            )

        customer = self.context["request"].user

        order_items = OrderItem.objects.filter(
            order__customer=customer,
            order__status=Order.Status.DELIVERED,
        )

        if item_id:
            purchased = order_items.filter(
                item_id=item_id,
            ).exists()

            if not purchased:
                raise serializers.ValidationError(
                    "You can review an item only after receiving it."
                )

        if package_id:
            purchased = order_items.filter(
                package_id=package_id,
            ).exists()

            if not purchased:
                raise serializers.ValidationError(
                    "You can review a package only after receiving it."
                )

        existing_review = Review.objects.filter(
            customer=customer,
        )

        if item_id:
            existing_review = existing_review.filter(
                item_id=item_id,
            )

        if package_id:
            existing_review = existing_review.filter(
                package_id=package_id,
            )

        if existing_review.exists():
            raise serializers.ValidationError(
                {
                    "detail": (
                        "You have already reviewed this product."
                    )
                }
            )

        return attrs

    def create(self, validated_data):

        item_id = validated_data.pop("item_id", None)
        package_id = validated_data.pop("package_id", None)

        request = self.context["request"]

        return Review.objects.create(
            customer=request.user,
            item_id=item_id,
            package_id=package_id,
            **validated_data,
        )

    def get_product_type(self, obj):

        if obj.item:
            return "ITEM"

        return "PACKAGE"

    def get_product_id(self, obj):

        if obj.item:
            return obj.item.id

        return obj.package.id

    def get_product_name(self, obj):

        if obj.item:
            return obj.item.name

        return obj.package.name

    def get_customer_name(self, obj):

        full_name = (
            f"{obj.customer.first_name} "
            f"{obj.customer.last_name}"
        ).strip()

        return (
            full_name
            or obj.customer.phone_number
        )


class AdminReviewSerializer(serializers.ModelSerializer):

    product_type = serializers.SerializerMethodField()

    product_id = serializers.SerializerMethodField()

    product_name = serializers.SerializerMethodField()

    customer_name = serializers.SerializerMethodField()

    class Meta:
        model = Review

        fields = (
            "id",
            "product_type",
            "product_id",
            "product_name",
            "customer_name",
            "rating",
            "review",
            "is_approved",
            "created_at",
            "updated_at",
        )

        read_only_fields = (
            "id",
            "product_type",
            "product_id",
            "product_name",
            "customer_name",
            "rating",
            "review",
            "created_at",
            "updated_at",
        )

    def get_product_type(self, obj):

        if obj.item:
            return "ITEM"

        return "PACKAGE"

    def get_product_id(self, obj):

        if obj.item:
            return obj.item.id

        return obj.package.id

    def get_product_name(self, obj):

        if obj.item:
            return obj.item.name

        return obj.package.name

    def get_customer_name(self, obj):

        full_name = (
            f"{obj.customer.first_name} "
            f"{obj.customer.last_name}"
        ).strip()

        return (
            full_name
            or obj.customer.phone_number
        )


class OrderListSerializer(serializers.ModelSerializer):
    total_items = serializers.SerializerMethodField()

    class Meta:
        model = Order

        fields = (
            "id",
            "status",
            "total_items",
            "subtotal",
            "delivery_charge",
            "discount_amount",
            "total_amount",
            "created_at",
        )

    def get_total_items(self, obj):
        return sum(
            order_item.quantity
            for order_item in obj.order_items.all()
        )

class OrderItemSerializer(serializers.ModelSerializer):

    class Meta:
        model = OrderItem

        fields = (
            "id",
            "product_type",
            "product_name",
            "product_slug",
            "quantity",
            "unit_price",
            "total_price",
            "created_at",
        )

class PaymentSerializer(serializers.ModelSerializer):

    class Meta:
        model = Payment

        fields = (
            "id",
            "amount",
            "method",
            "status",
            "transaction_id",
            "created_at",
            "updated_at",
        )

class OrderDetailSerializer(serializers.ModelSerializer):
    order_items = OrderItemSerializer(
        many=True,
        read_only=True,
    )

    total_items = serializers.SerializerMethodField()

    address = serializers.SerializerMethodField()

    payment = PaymentSerializer(
        read_only=True,
    )

    class Meta:
        model = Order

        fields = (
            "id",
            "status",
            "address",
            "order_items",
            "total_items",
            "payment",
            "subtotal",
            "discount_amount",
            "delivery_charge",
            "total_amount",
            "created_at",
            "updated_at",
        )

    def get_total_items(self, obj):
        return sum(
            order_item.quantity
            for order_item in obj.order_items.all()
        )

    def get_address(self, obj):
        return {
            "full_name": obj.full_name,
            "phone_number": obj.phone_number,
            "address_line_1": obj.address_line_1,
            "address_line_2": obj.address_line_2,
            "landmark": obj.landmark,
            "city": obj.city,
            "state": obj.state,
            "pincode": obj.pincode,
            "country": obj.country,
        }


class UpdateOrderStatusSerializer(serializers.Serializer):
    status = serializers.ChoiceField(
        choices=Order.Status.choices,
    )


class AdminOrderListSerializer(serializers.ModelSerializer):
    customer_name = serializers.SerializerMethodField()
    customer_phone = serializers.SerializerMethodField()
    total_items = serializers.SerializerMethodField()

    class Meta:
        model = Order

        fields = (
            "id",
            "customer_name",
            "customer_phone",
            "status",
            "total_items",
            "subtotal",
            "discount_amount",
            "delivery_charge",
            "total_amount",
            "created_at",
        )

    def get_customer_name(self, obj):
        full_name = (
            f"{obj.customer.first_name} "
            f"{obj.customer.last_name}"
        ).strip()

        return full_name or obj.customer.phone_number

    def get_customer_phone(self, obj):
        return obj.customer.phone_number

    def get_total_items(self, obj):
        return sum(
            order_item.quantity
            for order_item in obj.order_items.all()
        )


class OrderStatusHistorySerializer(serializers.ModelSerializer):
    changed_by = serializers.SerializerMethodField()

    class Meta:
        model = OrderStatusHistory

        fields = (
            "id",
            "previous_status",
            "new_status",
            "changed_by",
            "created_at",
        )

    def get_changed_by(self, obj):
        full_name = (
            f"{obj.changed_by.first_name} "
            f"{obj.changed_by.last_name}"
        ).strip()

        return {
            "id": obj.changed_by.id,
            "name": (
                full_name
                or obj.changed_by.phone_number
            ),
        }

class AdminOrderDetailSerializer(serializers.ModelSerializer):
    customer = serializers.SerializerMethodField()

    order_items = OrderItemSerializer(
        many=True,
        read_only=True,
    )

    total_items = serializers.SerializerMethodField()

    address = serializers.SerializerMethodField()

    status_history = OrderStatusHistorySerializer(
        many=True,
        read_only=True,
    )

    class Meta:
        model = Order

        fields = (
            "id",
            "customer",
            "status",
            "address",
            "order_items",
            "total_items",
            "subtotal",
            "discount_amount",
            "delivery_charge",
            "total_amount",
            "status_history",
            "created_at",
            "updated_at",
        )

    def get_customer(self, obj):
        full_name = (
            f"{obj.customer.first_name} "
            f"{obj.customer.last_name}"
        ).strip()

        return {
            "id": obj.customer.id,
            "name": full_name,
            "email": obj.customer.email,
            "phone_number": obj.customer.phone_number,
        }

    def get_total_items(self, obj):
        return sum(
            order_item.quantity
            for order_item in obj.order_items.all()
        )

    def get_address(self, obj):
        return {
            "full_name": obj.full_name,
            "phone_number": obj.phone_number,
            "address_line_1": obj.address_line_1,
            "address_line_2": obj.address_line_2,
            "landmark": obj.landmark,
            "city": obj.city,
            "state": obj.state,
            "pincode": obj.pincode,
            "country": obj.country,
        }

class CreatePaymentSerializer(serializers.Serializer):

    order_id = serializers.IntegerField(
        min_value=1,
    )

    method = serializers.ChoiceField(
        choices=Payment.Method.choices,
    )


class AdminPaymentListSerializer(serializers.ModelSerializer):
    order_id = serializers.IntegerField(
        source="order.id",
        read_only=True,
    )

    customer_name = serializers.SerializerMethodField()
    customer_phone = serializers.SerializerMethodField()

    class Meta:
        model = Payment

        fields = (
            "id",
            "order_id",
            "customer_name",
            "customer_phone",
            "amount",
            "method",
            "status",
            "transaction_id",
            "created_at",
            "updated_at",
        )

    def get_customer_name(self, obj):
        full_name = (
            f"{obj.order.customer.first_name} "
            f"{obj.order.customer.last_name}"
        ).strip()

        return (
            full_name
            or obj.order.customer.phone_number
        )

    def get_customer_phone(self, obj):
        return obj.order.customer.phone_number


class AdminPaymentDetailSerializer(serializers.ModelSerializer):
    order_id = serializers.IntegerField(
        source="order.id",
        read_only=True,
    )

    customer = serializers.SerializerMethodField()

    order_status = serializers.CharField(
        source="order.status",
        read_only=True,
    )

    order_total = serializers.DecimalField(
        source="order.total_amount",
        max_digits=12,
        decimal_places=2,
        read_only=True,
    )

    class Meta:
        model = Payment

        fields = (
            "id",
            "order_id",
            "customer",
            "order_status",
            "order_total",
            "amount",
            "method",
            "status",
            "transaction_id",
            "created_at",
            "updated_at",
        )

    def get_customer(self, obj):
        full_name = (
            f"{obj.order.customer.first_name} "
            f"{obj.order.customer.last_name}"
        ).strip()

        return {
            "id": obj.order.customer.id,
            "name": (
                full_name
                or obj.order.customer.phone_number
            ),
            "email": obj.order.customer.email,
            "phone_number": obj.order.customer.phone_number,
        }


class AdminRefundListSerializer(serializers.ModelSerializer):
    payment_id = serializers.IntegerField(
        source="payment.id",
        read_only=True,
    )

    order_id = serializers.IntegerField(
        source="payment.order.id",
        read_only=True,
    )

    customer_name = serializers.SerializerMethodField()

    class Meta:
        model = Refund

        fields = (
            "id",
            "payment_id",
            "order_id",
            "customer_name",
            "amount",
            "reason",
            "status",
            "refund_reference",
            "processed_by",
            "created_at",
            "updated_at",
        )

    def get_customer_name(self, obj):
        customer = obj.payment.order.customer

        full_name = (
            f"{customer.first_name} "
            f"{customer.last_name}"
        ).strip()

        return (
            full_name
            or customer.phone_number
        )


class AdminRefundDetailSerializer(serializers.ModelSerializer):
    payment_id = serializers.IntegerField(
        source="payment.id",
        read_only=True,
    )

    order_id = serializers.IntegerField(
        source="payment.order.id",
        read_only=True,
    )

    customer = serializers.SerializerMethodField()

    order_status = serializers.CharField(
        source="payment.order.status",
        read_only=True,
    )

    payment_amount = serializers.DecimalField(
        source="payment.amount",
        max_digits=12,
        decimal_places=2,
        read_only=True,
    )

    class Meta:
        model = Refund

        fields = (
            "id",
            "payment_id",
            "order_id",
            "customer",
            "order_status",
            "payment_amount",
            "amount",
            "reason",
            "status",
            "refund_reference",
            "processed_by",
            "created_at",
            "updated_at",
        )

    def get_customer(self, obj):
        customer = obj.payment.order.customer

        full_name = (
            f"{customer.first_name} "
            f"{customer.last_name}"
        ).strip()

        return {
            "id": customer.id,
            "name": (
                full_name
                or customer.phone_number
            ),
            "email": customer.email,
            "phone_number": customer.phone_number,
        }


class AdminReviewModerationSerializer(serializers.ModelSerializer):

    class Meta:
        model = Review

        fields = (
            "id",
            "is_approved",
        )

        read_only_fields = (
            "id",
        )