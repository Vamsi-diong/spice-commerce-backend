from django.db import transaction
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from decimal import Decimal
from apps.accounts.models import Address
from .permissions import IsOrderManagementStaff
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters
from .filters import AdminOrderFilter,AdminPaymentFilter,AdminRefundFilter
from collections import defaultdict
from apps.products.models import Item, Package
from .pagination import AdminListPagination
from .models import Cart, CartItem, Order, OrderItem,Payment,OrderStatusHistory,Refund
from .serializers import (
    AddCartItemSerializer,
    CartSerializer,
    UpdateCartItemSerializer,
    CheckoutSerializer,
    OrderListSerializer,
    OrderDetailSerializer,
    UpdateOrderStatusSerializer,
    AdminOrderListSerializer,
    AdminOrderDetailSerializer,
    CreatePaymentSerializer,
    AdminPaymentListSerializer,
    AdminPaymentDetailSerializer,
    OrderStatusHistorySerializer,
    AdminRefundDetailSerializer,
    AdminRefundListSerializer
)


class AddCartItemAPIView(generics.GenericAPIView):
    permission_classes = (
        permissions.IsAuthenticated,
    )

    serializer_class = AddCartItemSerializer

    def post(self, request):
        serializer = self.get_serializer(
            data=request.data,
        )
        serializer.is_valid(
            raise_exception=True,
        )

        item_id = serializer.validated_data.get("item_id")
        package_id = serializer.validated_data.get("package_id")
        quantity = serializer.validated_data["quantity"]

        cart, _ = Cart.objects.get_or_create(
            customer=request.user,
        )

        if item_id:
            try:
                item = Item.objects.get(
                    id=item_id,
                    is_active=True,
                    category__is_active=True,
                    category__collection__is_active=True,
                )
            except Item.DoesNotExist:
                return Response(
                    {
                        "detail": "Item not found or unavailable."
                    },
                    status=status.HTTP_404_NOT_FOUND,
                )

            if not item.in_stock:
                return Response(
                    {
                        "detail": "This item is currently out of stock."
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            cart_item, created = CartItem.objects.get_or_create(
                cart=cart,
                item=item,
                defaults={
                    "quantity": quantity,
                },
            )

            if not created:
                cart_item.quantity += quantity
                cart_item.save()

        else:
            try:
                package = Package.objects.get(
                    id=package_id,
                    is_active=True,
                )
            except Package.DoesNotExist:
                return Response(
                    {
                        "detail": "Package not found or unavailable."
                    },
                    status=status.HTTP_404_NOT_FOUND,
                )

            if not package.in_stock:
                return Response(
                    {
                        "detail": "This package is currently out of stock."
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            cart_item, created = CartItem.objects.get_or_create(
                cart=cart,
                package=package,
                defaults={
                    "quantity": quantity,
                },
            )

            if not created:
                cart_item.quantity += quantity
                cart_item.save()

        cart.refresh_from_db()

        return Response(
            CartSerializer(cart).data,
            status=(
                status.HTTP_201_CREATED
                if created
                else status.HTTP_200_OK
            ),
        )


class CartAPIView(generics.GenericAPIView):
    permission_classes = (
        permissions.IsAuthenticated,
    )

    serializer_class = CartSerializer

    def get(self, request):
        cart, _ = Cart.objects.get_or_create(
            customer=request.user,
        )

        cart = Cart.objects.prefetch_related(
            "cart_items__item",
            "cart_items__package",
        ).get(
            id=cart.id,
        )

        return Response(
            CartSerializer(cart).data,
            status=status.HTTP_200_OK,
        )


class UpdateCartItemAPIView(generics.GenericAPIView):
    permission_classes = (
        permissions.IsAuthenticated,
    )

    serializer_class = UpdateCartItemSerializer

    def get_cart_item(self, request, cart_item_id):
        try:
            return CartItem.objects.select_related(
                "cart",
                "item",
                "package",
            ).get(
                id=cart_item_id,
                cart__customer=request.user,
            )
        except CartItem.DoesNotExist:
            return None

    def get_updated_cart(self, cart_id):
        return Cart.objects.prefetch_related(
            "cart_items__item",
            "cart_items__package",
        ).get(
            id=cart_id,
        )

    def patch(self, request, cart_item_id):
        serializer = self.get_serializer(
            data=request.data,
        )
        serializer.is_valid(
            raise_exception=True,
        )

        cart_item = self.get_cart_item(
            request,
            cart_item_id,
        )

        if not cart_item:
            return Response(
                {
                    "detail": "Cart item not found."
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        quantity = serializer.validated_data["quantity"]

        cart_item.quantity = quantity
        cart_item.save()

        cart = self.get_updated_cart(
            cart_item.cart_id,
        )

        return Response(
            CartSerializer(cart).data,
            status=status.HTTP_200_OK,
        )

    def delete(self, request, cart_item_id):
        cart_item = self.get_cart_item(
            request,
            cart_item_id,
        )

        if not cart_item:
            return Response(
                {
                    "detail": "Cart item not found."
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        cart_id = cart_item.cart_id

        cart_item.delete()

        cart = self.get_updated_cart(
            cart_id,
        )

        return Response(
            CartSerializer(cart).data,
            status=status.HTTP_200_OK,
        )


class CheckoutAPIView(generics.GenericAPIView):
    permission_classes = (
        permissions.IsAuthenticated,
    )

    serializer_class = CheckoutSerializer

    @transaction.atomic
    def post(self, request):
        serializer = self.get_serializer(
            data=request.data,
        )
        serializer.is_valid(
            raise_exception=True,
        )

        address_id = serializer.validated_data[
            "address_id"
        ]

        # Validate selected address
        address = Address.objects.filter(
            id=address_id,
            user=request.user,
        ).first()

        if not address:
            return Response(
                {
                    "detail": "Address not found."
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        # Get customer's cart
        cart = Cart.objects.prefetch_related(
            "cart_items__item",
            "cart_items__package__package_items__item",
        ).filter(
            customer=request.user,
        ).first()

        if not cart or not cart.cart_items.exists():
            return Response(
                {
                    "detail": "Your cart is empty."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        checkout_items = []
        subtotal = Decimal("0.00")


        # -------------------------------------------------
        # STEP 1: VALIDATE CART AND CALCULATE TOTAL
        # -------------------------------------------------

        required_stock = defaultdict(int)

        for cart_item in cart.cart_items.all():

            product = cart_item.product

            if not product:
                return Response(
                    {
                        "detail": (
                            f"Cart item {cart_item.id} "
                            "has no valid product."
                        )
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            if not product.is_active:
                return Response(
                    {
                        "detail": (
                            f"{product.name} is no longer available."
                        )
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # ---------------------------------------------
            # INDIVIDUAL ITEM
            # ---------------------------------------------

            if cart_item.item:

                required_stock[cart_item.item.id] += (
                    cart_item.quantity
                )

            # ---------------------------------------------
            # PACKAGE
            # ---------------------------------------------

            elif cart_item.package:

                for package_item in (
                    cart_item.package.package_items.select_related(
                        "item"
                    ).all()
                ):

                    required_stock[package_item.item.id] += (
                        package_item.quantity
                        * cart_item.quantity
                    )

            # ---------------------------------------------
            # CALCULATE PRICE
            # ---------------------------------------------

            unit_price = product.selling_price

            total_price = (
                unit_price * cart_item.quantity
            )

            subtotal += total_price

            checkout_items.append(
                {
                    "cart_item": cart_item,
                    "product": product,
                    "unit_price": unit_price,
                    "total_price": total_price,
                }
            )


        # -------------------------------------------------
        # LOCK AND VALIDATE TOTAL REQUIRED STOCK
        # -------------------------------------------------

        locked_items = {
            item.id: item
            for item in Item.objects.select_for_update().filter(
                id__in=required_stock.keys(),
                is_active=True,
            )
        }


        for item_id, quantity_required in required_stock.items():

            item = locked_items.get(item_id)

            if not item:
                return Response(
                    {
                        "detail": (
                            "One or more items are no longer available."
                        )
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            if quantity_required > item.stock_quantity:
                return Response(
                    {
                        "detail": (
                            f"Only {item.stock_quantity} units of "
                            f"{item.name} are available, but "
                            f"{quantity_required} units are required "
                            "for your cart."
                        )
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

        # -------------------------------------------------
        # STEP 2: FREE DELIVERY
        # -------------------------------------------------

        delivery_charge = Decimal("0.00")

        total_amount = (
            subtotal + delivery_charge
        )

        # -------------------------------------------------
        # STEP 3: CREATE ORDER
        # -------------------------------------------------

        order = Order.objects.create(
            customer=request.user,
            address=address,

            # Address snapshot
            full_name=address.full_name,
            phone_number=address.phone_number,
            address_line_1=address.address_line_1,
            address_line_2=address.address_line_2,
            landmark=address.landmark,
            city=address.city,
            state=address.state,
            pincode=address.pincode,
            country=address.country,

            status=Order.Status.PENDING,

            subtotal=subtotal,
            delivery_charge=delivery_charge,
            total_amount=total_amount,
        )

        # -------------------------------------------------
        # STEP 4: CREATE ORDER ITEMS
        # -------------------------------------------------

        for checkout_item in checkout_items:

            cart_item = checkout_item["cart_item"]
            product = checkout_item["product"]

            OrderItem.objects.create(
                order=order,

                item=cart_item.item,
                package=cart_item.package,

                product_type=(
                    OrderItem.ProductType.ITEM
                    if cart_item.item
                    else OrderItem.ProductType.PACKAGE
                ),

                product_name=product.name,
                product_slug=product.slug,

                quantity=cart_item.quantity,

                unit_price=checkout_item[
                    "unit_price"
                ],

                total_price=checkout_item[
                    "total_price"
                ],
            )

        # -------------------------------------------------
        # STEP 5: REDUCE STOCK
        # -------------------------------------------------

        for item_id, quantity_required in required_stock.items():

            item = locked_items[item_id]

            item.stock_quantity -= quantity_required

            item.save(
                update_fields=[
                    "stock_quantity",
                ]
            )

        # -------------------------------------------------
        # STEP 6: CLEAR CART
        # -------------------------------------------------

        cart.cart_items.all().delete()

        # -------------------------------------------------
        # STEP 7: RETURN ORDER
        # -------------------------------------------------

        return Response(
            {
                "message": (
                    "Order created successfully."
                ),

                "order_id": order.id,

                "status": order.status,

                "address": {
                    "full_name": order.full_name,
                    "phone_number": order.phone_number,
                    "address_line_1": (
                        order.address_line_1
                    ),
                    "address_line_2": (
                        order.address_line_2
                    ),
                    "landmark": order.landmark,
                    "city": order.city,
                    "state": order.state,
                    "pincode": order.pincode,
                    "country": order.country,
                },

                "subtotal": order.subtotal,
                "delivery_charge": (
                    order.delivery_charge
                ),
                "total_amount": order.total_amount,

                "items": [
                    {
                        "product_type": item.product_type,
                        "product_name": item.product_name,
                        "product_slug": item.product_slug,
                        "quantity": item.quantity,
                        "unit_price": item.unit_price,
                        "total_price": item.total_price,
                    }
                    for item in order.order_items.all()
                ],
            },
            status=status.HTTP_201_CREATED,
        )


class OrderListAPIView(generics.ListAPIView):
    permission_classes = (
        permissions.IsAuthenticated,
    )

    serializer_class = OrderListSerializer

    def get_queryset(self):
        return Order.objects.filter(
            customer=self.request.user,
        ).prefetch_related(
            "order_items",
        )

class OrderDetailAPIView(generics.RetrieveAPIView):
    permission_classes = (
        permissions.IsAuthenticated,
    )

    serializer_class = OrderDetailSerializer
    lookup_field = "id"

    def get_queryset(self):
        return Order.objects.filter(
            customer=self.request.user,
        ).prefetch_related(
            "order_items",
        )

class CancelOrderAPIView(generics.GenericAPIView):
    permission_classes = (
        permissions.IsAuthenticated,
    )

    @transaction.atomic
    def post(self, request, id):

        order = Order.objects.select_for_update().prefetch_related(
            "order_items__item",
            "order_items__package__package_items__item",
        ).filter(
            id=id,
            customer=request.user,
        ).first()

        if not order:
            return Response(
                {
                    "detail": "Order not found."
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        # Check whether cancellation is allowed
        allowed_statuses = (
            Order.Status.PENDING,
            Order.Status.CONFIRMED,
        )

        if order.status not in allowed_statuses:
            return Response(
                {
                    "detail": (
                        f"Order cannot be cancelled when "
                        f"its status is {order.status}."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # -------------------------------------------------
        # CHECK PAYMENT
        # -------------------------------------------------

        # -------------------------------------------------
        # CHECK PAYMENT / CREATE REFUND
        # -------------------------------------------------

        payment = getattr(order, "payment", None)

        if payment and payment.status == Payment.Status.SUCCESS:

            # Prevent duplicate refund records
            existing_refund = (
                Refund.objects
                .filter(
                    payment=payment,
                    status__in=[
                        Refund.Status.PENDING,
                        Refund.Status.SUCCESS,
                    ],
                )
                .first()
            )

            if not existing_refund:

                Refund.objects.create(
                    payment=payment,
                    amount=payment.amount,
                    reason="Order cancelled by customer.",
                    status=Refund.Status.SUCCESS,
                    processed_by=None,
                )

            payment.status = Payment.Status.REFUNDED

            payment.save(
                update_fields=[
                    "status",
                    "updated_at",
                ]
            )

        # -------------------------------------------------
        # RESTORE STOCK
        # -------------------------------------------------

        restore_stock = {}

        for order_item in order.order_items.all():

            # Individual item
            if order_item.item:

                item_id = order_item.item.id

                restore_stock[item_id] = (
                    restore_stock.get(item_id, 0)
                    + order_item.quantity
                )

            # Package
            elif order_item.package:

                for package_item in (
                    order_item.package.package_items.all()
                ):

                    item_id = package_item.item_id

                    stock_to_restore = (
                        package_item.quantity
                        * order_item.quantity
                    )

                    restore_stock[item_id] = (
                        restore_stock.get(item_id, 0)
                        + stock_to_restore
                    )


        # Lock the affected items
        locked_items = {
            item.id: item
            for item in Item.objects.select_for_update().filter(
                id__in=restore_stock.keys(),
            )
        }


        # Restore stock
        for item_id, quantity_to_restore in restore_stock.items():

            item = locked_items.get(item_id)

            if not item:
                continue

            item.stock_quantity += quantity_to_restore

            item.save(
                update_fields=[
                    "stock_quantity",
                ]
            )

        # Change order status
# -------------------------------------------------
# CHANGE ORDER STATUS
# -------------------------------------------------

        previous_status = order.status

        order.status = Order.Status.CANCELLED

        order.save(
            update_fields=[
                "status",
                "updated_at",
            ]
        )

        # -------------------------------------------------
        # CREATE STATUS HISTORY
        # -------------------------------------------------

        OrderStatusHistory.objects.create(
            order=order,
            previous_status=previous_status,
            new_status=order.status,
            changed_by=request.user,
        )

        return Response(
            {
                "message": "Order cancelled successfully.",
                "order_id": order.id,
                "status": order.status,
            },
            status=status.HTTP_200_OK,
        )



class UpdateOrderStatusAPIView(generics.GenericAPIView):
    permission_classes = (
        IsOrderManagementStaff,
    )

    serializer_class = UpdateOrderStatusSerializer

    @transaction.atomic
    def patch(self, request, id):

        # ---------------------------------------------
        # 1. VALIDATE REQUEST DATA
        # ---------------------------------------------

        serializer = self.get_serializer(
            data=request.data,
        )

        serializer.is_valid(
            raise_exception=True,
        )

        new_status = serializer.validated_data["status"]

        # ---------------------------------------------
        # 2. GET ORDER
        # ---------------------------------------------

        order = (
            Order.objects
            .select_for_update()
            .filter(id=id)
            .first()
        )

        if not order:
            return Response(
                {
                    "detail": "Order not found."
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        # ---------------------------------------------
        # 3. PREVENT SAME STATUS
        # ---------------------------------------------

        if order.status == new_status:
            return Response(
                {
                    "detail": (
                        f"Order is already in "
                        f"{order.status} status."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # ---------------------------------------------
        # 4. VALID STATUS TRANSITIONS
        # ---------------------------------------------

        valid_transitions = {

            Order.Status.PENDING: (
                Order.Status.CONFIRMED,
            ),

            Order.Status.CONFIRMED: (
                Order.Status.PROCESSING,
            ),

            Order.Status.PROCESSING: (
                Order.Status.SHIPPED,
            ),

            Order.Status.SHIPPED: (
                Order.Status.DELIVERED,
            ),

            Order.Status.DELIVERED: (),

            Order.Status.CANCELLED: (),
        }

        allowed_next_statuses = valid_transitions.get(
            order.status,
            (),
        )

        # ---------------------------------------------
        # 5. CHECK VALID TRANSITION
        # ---------------------------------------------

        if new_status not in allowed_next_statuses:
            return Response(
                {
                    "detail": (
                        f"Cannot change order status "
                        f"from {order.status} "
                        f"to {new_status}."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # ---------------------------------------------
        # 6. CHECK PAYMENT BEFORE CONFIRMING
        # ---------------------------------------------

        if new_status == Order.Status.CONFIRMED:

            payment = (
                Payment.objects
                .select_for_update()
                .filter(order=order)
                .first()
            )

            # -----------------------------------------
            # PAYMENT MUST EXIST
            # -----------------------------------------

            if not payment:
                return Response(
                    {
                        "detail": (
                            "Order cannot be confirmed "
                            "because no payment exists."
                        )
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # -----------------------------------------
            # ONLINE PAYMENT
            # -----------------------------------------

            if payment.method == Payment.Method.ONLINE:

                if payment.status != Payment.Status.SUCCESS:
                    return Response(
                        {
                            "detail": (
                                "Online payment must be "
                                "successful before the "
                                "order can be confirmed."
                            ),
                            "payment_status": payment.status,
                        },
                        status=status.HTTP_400_BAD_REQUEST,
                    )

            # -----------------------------------------
            # COD PAYMENT
            # -----------------------------------------

            elif payment.method == Payment.Method.COD:

                if payment.status == Payment.Status.SUCCESS:
                    return Response(
                        {
                            "detail": (
                                "COD payment cannot be "
                                "successful before the "
                                "order is delivered."
                            )
                        },
                        status=status.HTTP_400_BAD_REQUEST,
                    )

                if payment.status == Payment.Status.REFUNDED:
                    return Response(
                        {
                            "detail": (
                                "A refunded payment cannot "
                                "be associated with a "
                                "confirmed order."
                            )
                        },
                        status=status.HTTP_400_BAD_REQUEST,
                    )

                if payment.status != Payment.Status.PENDING:
                    return Response(
                        {
                            "detail": (
                                "COD payment must be pending "
                                "before the order can be "
                                "confirmed."
                            ),
                            "payment_status": payment.status,
                        },
                        status=status.HTTP_400_BAD_REQUEST,
                    )

        # ---------------------------------------------
        # 7. SAVE PREVIOUS STATUS
        # ---------------------------------------------

        previous_status = order.status

        # ---------------------------------------------
        # 8. UPDATE ORDER STATUS
        # ---------------------------------------------

        order.status = new_status

        order.save(
            update_fields=[
                "status",
                "updated_at",
            ]
        )

        # ---------------------------------------------
        # 9. CREATE STATUS HISTORY
        # ---------------------------------------------

        OrderStatusHistory.objects.create(
            order=order,
            previous_status=previous_status,
            new_status=new_status,
            changed_by=request.user,
        )

        # ---------------------------------------------
        # 10. RESPONSE
        # ---------------------------------------------

        return Response(
            {
                "message": (
                    "Order status updated successfully."
                ),
                "order_id": order.id,
                "previous_status": previous_status,
                "status": order.status,
            },
            status=status.HTTP_200_OK,
        )



class AdminOrderListAPIView(generics.ListAPIView):
    permission_classes = (
        IsOrderManagementStaff,
    )

    serializer_class = AdminOrderListSerializer

    pagination_class = AdminListPagination

    filter_backends = (
        DjangoFilterBackend,
        filters.SearchFilter,
    )

    filterset_class = AdminOrderFilter

    search_fields = (
        "id",
        "customer__first_name",
        "customer__last_name",
        "customer__email",
        "customer__phone_number",
        "full_name",
        "phone_number",
        "city",
        "pincode",
    )

    def get_queryset(self):

        return (
            Order.objects
            .select_related(
                "customer",
                "address",
            )
            .prefetch_related(
                "order_items",
            )
            .order_by("-created_at")
        )


class AdminOrderDetailAPIView(generics.RetrieveAPIView):
    permission_classes = (
        IsOrderManagementStaff,
    )

    serializer_class = AdminOrderDetailSerializer

    lookup_url_kwarg = "id"

    def get_queryset(self):

        return (
            Order.objects
            .select_related(
                "customer",
                "payment",
                "address",
            )
            .prefetch_related(
                "order_items",
                "status_history__changed_by",
            )
        )

class CreatePaymentAPIView(generics.GenericAPIView):
    permission_classes = (
        permissions.IsAuthenticated,
    )

    serializer_class = CreatePaymentSerializer

    @transaction.atomic
    def post(self, request):

        # ---------------------------------------------
        # 1. VALIDATE REQUEST DATA
        # ---------------------------------------------

        serializer = self.get_serializer(
            data=request.data,
        )

        serializer.is_valid(
            raise_exception=True,
        )

        order_id = serializer.validated_data["order_id"]
        method = serializer.validated_data["method"]

        # ---------------------------------------------
        # 2. GET CUSTOMER ORDER
        # ---------------------------------------------

        order = (
            Order.objects
            .select_for_update()
            .filter(
                id=order_id,
                customer=request.user,
            )
            .first()
        )

        if not order:
            return Response(
                {
                    "detail": "Order not found."
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        # ---------------------------------------------
        # 3. CHECK ORDER STATUS
        # ---------------------------------------------

        if order.status == Order.Status.CANCELLED:
            return Response(
                {
                    "detail": (
                        "Payment cannot be created for "
                        "a cancelled order."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        if order.status != Order.Status.PENDING:
            return Response(
                {
                    "detail": (
                        "Payment can only be created for "
                        "a pending order."
                    ),
                    "order_status": order.status,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # ---------------------------------------------
        # 4. CHECK WHETHER PAYMENT ALREADY EXISTS
        # ---------------------------------------------

        existing_payment = (
            Payment.objects
            .filter(order=order)
            .first()
        )

        if existing_payment:
            return Response(
                {
                    "detail": (
                        "Payment already exists for "
                        "this order."
                    ),
                    "payment_id": existing_payment.id,
                    "payment_status": existing_payment.status,
                    "payment_method": existing_payment.method,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # ---------------------------------------------
        # 5. VALIDATE ORDER TOTAL
        # ---------------------------------------------

        if order.total_amount <= 0:
            return Response(
                {
                    "detail": (
                        "Payment cannot be created for "
                        "an invalid order amount."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # ---------------------------------------------
        # 6. CREATE PAYMENT
        # ---------------------------------------------

        payment = Payment.objects.create(
            order=order,
            amount=order.total_amount,
            method=method,
            status=Payment.Status.PENDING,
        )

        # ---------------------------------------------
        # 7. RESPONSE
        # ---------------------------------------------

        return Response(
            {
                "message": (
                    "Payment created successfully."
                ),
                "payment_id": payment.id,
                "order_id": order.id,
                "amount": payment.amount,
                "method": payment.method,
                "status": payment.status,
                "transaction_id": payment.transaction_id,
            },
            status=status.HTTP_201_CREATED,
        )
    

class PaymentSuccessAPIView(generics.GenericAPIView):
    permission_classes = (
        permissions.IsAuthenticated,
    )

    @transaction.atomic
    def post(self, request, payment_id):

        # ---------------------------------------------
        # 1. GET PAYMENT
        # ---------------------------------------------

        payment = (
            Payment.objects
            .select_for_update()
            .select_related("order")
            .filter(
                id=payment_id,
                order__customer=request.user,
            )
            .first()
        )

        if not payment:
            return Response(
                {
                    "detail": "Payment not found."
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        order = payment.order

        # ---------------------------------------------
        # 2. CHECK PAYMENT METHOD
        # ---------------------------------------------

        if payment.method != Payment.Method.ONLINE:
            return Response(
                {
                    "detail": (
                        "Only online payments can be "
                        "marked as successful through "
                        "this API."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # ---------------------------------------------
        # 3. CHECK PAYMENT AMOUNT
        # ---------------------------------------------

        if payment.amount != order.total_amount:
            return Response(
                {
                    "detail": (
                        "Payment amount does not match "
                        "the order total."
                    ),
                    "payment_amount": payment.amount,
                    "order_total": order.total_amount,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # ---------------------------------------------
        # 4. CHECK PAYMENT STATUS
        # ---------------------------------------------

        if payment.status == Payment.Status.SUCCESS:
            return Response(
                {
                    "detail": "Payment is already successful."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        if payment.status == Payment.Status.REFUNDED:
            return Response(
                {
                    "detail": (
                        "A refunded payment cannot be "
                        "marked as successful."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        if payment.status != Payment.Status.PENDING:
            return Response(
                {
                    "detail": (
                        "Only a pending payment can be "
                        "marked as successful."
                    ),
                    "payment_status": payment.status,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # ---------------------------------------------
        # 5. CHECK ORDER STATUS
        # ---------------------------------------------

        if order.status == Order.Status.CANCELLED:
            return Response(
                {
                    "detail": (
                        "Payment cannot be completed for "
                        "a cancelled order."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        if order.status != Order.Status.PENDING:
            return Response(
                {
                    "detail": (
                        "Payment can only confirm an order "
                        "that is currently pending."
                    ),
                    "order_status": order.status,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # ---------------------------------------------
        # 6. MARK PAYMENT SUCCESS
        # ---------------------------------------------

        payment.status = Payment.Status.SUCCESS

        payment.save(
            update_fields=[
                "status",
                "updated_at",
            ]
        )

        # ---------------------------------------------
        # 7. CONFIRM ORDER
        # ---------------------------------------------

        previous_status = order.status

        order.status = Order.Status.CONFIRMED

        order.save(
            update_fields=[
                "status",
                "updated_at",
            ]
        )

        # ---------------------------------------------
        # 8. CREATE ORDER STATUS HISTORY
        # ---------------------------------------------

        OrderStatusHistory.objects.create(
            order=order,
            previous_status=previous_status,
            new_status=order.status,
            changed_by=request.user,
        )

        # ---------------------------------------------
        # 9. RESPONSE
        # ---------------------------------------------

        return Response(
            {
                "message": (
                    "Payment successful and order "
                    "confirmed successfully."
                ),
                "payment_id": payment.id,
                "order_id": order.id,
                "payment_status": payment.status,
                "order_status": order.status,
                "amount": payment.amount,
                "method": payment.method,
            },
            status=status.HTTP_200_OK,
        )


class PaymentFailureAPIView(generics.GenericAPIView):
    permission_classes = (
        permissions.IsAuthenticated,
    )

    @transaction.atomic
    def post(self, request, payment_id):

        # ---------------------------------------------
        # 1. GET PAYMENT
        # ---------------------------------------------

        payment = (
            Payment.objects
            .select_for_update()
            .select_related("order")
            .filter(
                id=payment_id,
                order__customer=request.user,
            )
            .first()
        )

        if not payment:
            return Response(
                {
                    "detail": "Payment not found."
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        order = payment.order

        # ---------------------------------------------
        # 2. CHECK PAYMENT METHOD
        # ---------------------------------------------

        if payment.method != Payment.Method.ONLINE:
            return Response(
                {
                    "detail": (
                        "Only online payments can be "
                        "marked as failed through this API."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # ---------------------------------------------
        # 3. CHECK PAYMENT STATUS
        # ---------------------------------------------

        if payment.status == Payment.Status.SUCCESS:
            return Response(
                {
                    "detail": (
                        "A successful payment cannot be "
                        "marked as failed."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        if payment.status == Payment.Status.REFUNDED:
            return Response(
                {
                    "detail": (
                        "A refunded payment cannot be "
                        "marked as failed."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        if payment.status == Payment.Status.FAILED:
            return Response(
                {
                    "detail": "Payment is already marked as failed."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        if payment.status != Payment.Status.PENDING:
            return Response(
                {
                    "detail": (
                        "Only a pending payment can be "
                        "marked as failed."
                    ),
                    "payment_status": payment.status,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # ---------------------------------------------
        # 4. CHECK ORDER STATUS
        # ---------------------------------------------

        if order.status == Order.Status.CANCELLED:
            return Response(
                {
                    "detail": (
                        "Payment cannot be marked as failed "
                        "for a cancelled order."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        if order.status != Order.Status.PENDING:
            return Response(
                {
                    "detail": (
                        "Payment can only be marked as failed "
                        "while the order is pending."
                    ),
                    "order_status": order.status,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # ---------------------------------------------
        # 5. CALCULATE STOCK TO RESTORE
        # ---------------------------------------------

        restore_stock = defaultdict(int)

        order_items = (
            order.order_items
            .select_related("item")
            .prefetch_related(
                "package__package_items__item"
            )
            .all()
        )

        for order_item in order_items:

            # Individual item
            if order_item.item:

                restore_stock[order_item.item.id] += (
                    order_item.quantity
                )

            # Package
            elif order_item.package:

                for package_item in (
                    order_item.package.package_items.all()
                ):

                    restore_stock[package_item.item_id] += (
                        package_item.quantity
                        * order_item.quantity
                    )

        # ---------------------------------------------
        # 6. LOCK ITEMS
        # ---------------------------------------------

        locked_items = {
            item.id: item
            for item in Item.objects.select_for_update().filter(
                id__in=restore_stock.keys(),
            )
        }

        # ---------------------------------------------
        # 7. RESTORE STOCK
        # ---------------------------------------------

        for item_id, quantity_to_restore in restore_stock.items():

            item = locked_items.get(item_id)

            if not item:
                continue

            item.stock_quantity += quantity_to_restore

            item.save(
                update_fields=[
                    "stock_quantity",
                ]
            )

        # ---------------------------------------------
        # 8. MARK PAYMENT FAILED
        # ---------------------------------------------

        payment.status = Payment.Status.FAILED

        payment.save(
            update_fields=[
                "status",
                "updated_at",
            ]
        )

        # ---------------------------------------------
        # 9. RESPONSE
        # ---------------------------------------------

        return Response(
            {
                "message": (
                    "Payment marked as failed and "
                    "stock restored successfully."
                ),
                "payment_id": payment.id,
                "order_id": order.id,
                "payment_status": payment.status,
                "order_status": order.status,
                "amount": payment.amount,
                "method": payment.method,
            },
            status=status.HTTP_200_OK,
        )



class CollectCODPaymentAPIView(generics.GenericAPIView):
    permission_classes = (
        IsOrderManagementStaff,
    )

    @transaction.atomic
    def post(self, request, payment_id):

        # ---------------------------------------------
        # 1. GET PAYMENT
        # ---------------------------------------------

        payment = (
            Payment.objects
            .select_for_update()
            .select_related("order")
            .filter(
                id=payment_id,
            )
            .first()
        )

        if not payment:
            return Response(
                {
                    "detail": "Payment not found."
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        order = payment.order

        # ---------------------------------------------
        # 2. PAYMENT METHOD CHECK
        # ---------------------------------------------

        if payment.method != Payment.Method.COD:
            return Response(
                {
                    "detail": (
                        "This payment is not a COD payment."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # ---------------------------------------------
        # 3. PAYMENT AMOUNT CHECK
        # ---------------------------------------------

        if payment.amount != order.total_amount:
            return Response(
                {
                    "detail": (
                        "Payment amount does not match "
                        "the order total."
                    ),
                    "payment_amount": payment.amount,
                    "order_total": order.total_amount,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # ---------------------------------------------
        # 4. PAYMENT STATUS CHECK
        # ---------------------------------------------

        if payment.status == Payment.Status.SUCCESS:
            return Response(
                {
                    "detail": "Payment is already successful."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        if payment.status == Payment.Status.REFUNDED:
            return Response(
                {
                    "detail": (
                        "A refunded payment cannot be "
                        "collected."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        if payment.status != Payment.Status.PENDING:
            return Response(
                {
                    "detail": (
                        "Only a pending COD payment "
                        "can be collected."
                    ),
                    "payment_status": payment.status,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # ---------------------------------------------
        # 5. ORDER STATUS CHECK
        # ---------------------------------------------

        if order.status != Order.Status.DELIVERED:
            return Response(
                {
                    "detail": (
                        "COD payment can only be collected "
                        "after the order is delivered."
                    ),
                    "order_status": order.status,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # ---------------------------------------------
        # 6. MARK PAYMENT SUCCESS
        # ---------------------------------------------

        payment.status = Payment.Status.SUCCESS

        payment.save(
            update_fields=[
                "status",
                "updated_at",
            ]
        )

        # ---------------------------------------------
        # 7. RESPONSE
        # ---------------------------------------------

        return Response(
            {
                "message": (
                    "COD payment collected successfully."
                ),
                "payment_id": payment.id,
                "order_id": order.id,
                "payment_status": payment.status,
                "order_status": order.status,
                "amount": payment.amount,
                "method": payment.method,
            },
            status=status.HTTP_200_OK,
        )



class AdminPaymentSuccessAPIView(generics.GenericAPIView):
    permission_classes = (
        IsOrderManagementStaff,
    )

    @transaction.atomic
    def post(self, request, payment_id):

        # ---------------------------------------------
        # 1. GET PAYMENT
        # ---------------------------------------------

        payment = (
            Payment.objects
            .select_for_update()
            .select_related("order")
            .filter(
                id=payment_id,
            )
            .first()
        )

        if not payment:
            return Response(
                {
                    "detail": "Payment not found."
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        order = payment.order

        # ---------------------------------------------
        # 2. CHECK PAYMENT METHOD
        # ---------------------------------------------

        if payment.method != Payment.Method.ONLINE:
            return Response(
                {
                    "detail": (
                        "Only online payments can be "
                        "confirmed through this API."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # ---------------------------------------------
        # 3. CHECK PAYMENT AMOUNT
        # ---------------------------------------------

        if payment.amount != order.total_amount:
            return Response(
                {
                    "detail": (
                        "Payment amount does not match "
                        "the order total."
                    ),
                    "payment_amount": payment.amount,
                    "order_total": order.total_amount,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # ---------------------------------------------
        # 4. CHECK PAYMENT STATUS
        # ---------------------------------------------

        if payment.status == Payment.Status.SUCCESS:
            return Response(
                {
                    "detail": (
                        "Payment is already successful."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        if payment.status == Payment.Status.REFUNDED:
            return Response(
                {
                    "detail": (
                        "A refunded payment cannot be "
                        "marked as successful."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        if payment.status != Payment.Status.PENDING:
            return Response(
                {
                    "detail": (
                        "Only a pending payment can be "
                        "confirmed by an admin."
                    ),
                    "payment_status": payment.status,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # ---------------------------------------------
        # 5. CHECK ORDER STATUS
        # ---------------------------------------------

        if order.status == Order.Status.CANCELLED:
            return Response(
                {
                    "detail": (
                        "Payment cannot be confirmed for "
                        "a cancelled order."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        if order.status != Order.Status.PENDING:
            return Response(
                {
                    "detail": (
                        "Payment can only confirm an order "
                        "that is currently pending."
                    ),
                    "order_status": order.status,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # ---------------------------------------------
        # 6. MARK PAYMENT SUCCESS
        # ---------------------------------------------

        payment.status = Payment.Status.SUCCESS

        payment.save(
            update_fields=[
                "status",
                "updated_at",
            ]
        )

        # ---------------------------------------------
        # 7. CONFIRM ORDER
        # ---------------------------------------------

        previous_status = order.status

        order.status = Order.Status.CONFIRMED

        order.save(
            update_fields=[
                "status",
                "updated_at",
            ]
        )

        # ---------------------------------------------
        # 8. CREATE ORDER STATUS HISTORY
        # ---------------------------------------------

        OrderStatusHistory.objects.create(
            order=order,
            previous_status=previous_status,
            new_status=order.status,
            changed_by=request.user,
        )

        # ---------------------------------------------
        # 9. RESPONSE
        # ---------------------------------------------

        return Response(
            {
                "message": (
                    "Payment confirmed and order "
                    "confirmed successfully."
                ),
                "payment_id": payment.id,
                "order_id": order.id,
                "payment_status": payment.status,
                "order_status": order.status,
                "amount": payment.amount,
                "method": payment.method,
            },
            status=status.HTTP_200_OK,
        )

class AdminPaymentListAPIView(generics.ListAPIView):
    permission_classes = (
        IsOrderManagementStaff,
    )

    serializer_class = AdminPaymentListSerializer

    pagination_class = AdminListPagination

    filter_backends = (
        DjangoFilterBackend,
        filters.SearchFilter,
    )

    filterset_class = AdminPaymentFilter

    search_fields = (
        "id",
        "order__id",
        "order__customer__first_name",
        "order__customer__last_name",
        "order__customer__email",
        "order__customer__phone_number",
        "transaction_id",
    )

    def get_queryset(self):

        return (
            Payment.objects
            .select_related(
                "order",
                "order__customer",
            )
            .order_by("-created_at")
        )

class AdminPaymentDetailAPIView(generics.RetrieveAPIView):
    permission_classes = (
        IsOrderManagementStaff,
    )

    serializer_class = AdminPaymentDetailSerializer

    lookup_url_kwarg = "payment_id"

    def get_queryset(self):
        return (
            Payment.objects
            .select_related(
                "order",
                "order__customer",
            )
        )

class AdminPaymentFailureAPIView(generics.GenericAPIView):
    permission_classes = (
        IsOrderManagementStaff,
    )

    @transaction.atomic
    def post(self, request, payment_id):

        payment = (
            Payment.objects
            .select_for_update()
            .select_related("order")
            .filter(id=payment_id)
            .first()
        )

        if not payment:
            return Response(
                {
                    "detail": "Payment not found."
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        order = payment.order

        # ---------------------------------------------
        # CHECK CURRENT PAYMENT STATUS
        # ---------------------------------------------

        if payment.status == Payment.Status.SUCCESS:
            return Response(
                {
                    "detail": (
                        "A successful payment cannot be "
                        "marked as failed."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        if payment.status == Payment.Status.REFUNDED:
            return Response(
                {
                    "detail": (
                        "A refunded payment cannot be "
                        "marked as failed."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # ---------------------------------------------
        # CHECK ORDER STATUS
        # ---------------------------------------------

        if order.status != Order.Status.PENDING:
            return Response(
                {
                    "detail": (
                        "Payment can only be marked as "
                        "failed while the order is pending."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # ---------------------------------------------
        # MARK PAYMENT FAILED
        # ---------------------------------------------

        payment.status = Payment.Status.FAILED

        payment.save(
            update_fields=[
                "status",
                "updated_at",
            ]
        )

        # ---------------------------------------------
        # RESPONSE
        # ---------------------------------------------

        return Response(
            {
                "message": (
                    "Payment marked as failed successfully."
                ),
                "payment_id": payment.id,
                "order_id": order.id,
                "payment_status": payment.status,
                "order_status": order.status,
                "amount": payment.amount,
                "method": payment.method,
            },
            status=status.HTTP_200_OK,
        )

class AdminOrderStatusHistoryAPIView(generics.ListAPIView):
    permission_classes = (
        IsOrderManagementStaff,
    )

    serializer_class = OrderStatusHistorySerializer

    def get_queryset(self):
        allowed_roles = (
            self.request.user.Role.ADMIN,
            self.request.user.Role.MANAGER,
            self.request.user.Role.STAFF,
        )

        if self.request.user.role not in allowed_roles:
            return OrderStatusHistory.objects.none()

        order_id = self.kwargs["id"]

        return (
            OrderStatusHistory.objects
            .select_related(
                "order",
                "changed_by",
            )
            .filter(
                order_id=order_id,
            )
            .order_by("created_at")
        )
    

class AdminRefundAPIView(generics.GenericAPIView):
    permission_classes = (
        IsOrderManagementStaff,
    )

    serializer_class = AdminRefundDetailSerializer

    @transaction.atomic
    def post(self, request, payment_id):

        # ---------------------------------------------
        # GET PAYMENT
        # ---------------------------------------------

        payment = (
            Payment.objects
            .select_for_update()
            .select_related(
                "order",
                "order__customer",
            )
            .filter(
                id=payment_id,
            )
            .first()
        )

        if not payment:
            return Response(
                {
                    "detail": "Payment not found."
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        order = payment.order

        # ---------------------------------------------
        # PAYMENT STATUS CHECK
        # ---------------------------------------------

        if payment.status != Payment.Status.SUCCESS:
            return Response(
                {
                    "detail": (
                        "Only successful payments "
                        "can be refunded."
                    ),
                    "payment_status": payment.status,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # ---------------------------------------------
        # CHECK EXISTING REFUNDS
        # ---------------------------------------------

        existing_refund = (
            Refund.objects
            .filter(
                payment=payment,
                status__in=[
                    Refund.Status.PENDING,
                    Refund.Status.SUCCESS,
                ],
            )
            .first()
        )

        if existing_refund:
            return Response(
                {
                    "detail": (
                        "A refund already exists "
                        "for this payment."
                    ),
                    "refund_id": existing_refund.id,
                    "refund_status": existing_refund.status,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # ---------------------------------------------
        # VALIDATE PAYMENT AMOUNT
        # ---------------------------------------------

        if payment.amount != order.total_amount:
            return Response(
                {
                    "detail": (
                        "Payment amount does not match "
                        "the order total."
                    ),
                    "payment_amount": payment.amount,
                    "order_total": order.total_amount,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # ---------------------------------------------
        # GET REFUND REASON
        # ---------------------------------------------

        reason = request.data.get(
            "reason",
            "",
        ).strip()

        if len(reason) > 255:
            return Response(
                {
                    "detail": (
                        "Refund reason cannot exceed "
                        "255 characters."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        if payment.amount <= 0:
            return Response(
                {
                    "detail": (
                        "Refund cannot be processed for "
                        "an invalid payment amount."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # ---------------------------------------------
        # CREATE REFUND
        # ---------------------------------------------

        refund = Refund.objects.create(
            payment=payment,
            amount=payment.amount,
            reason=reason,
            status=Refund.Status.SUCCESS,
            processed_by=request.user,
        )

        # ---------------------------------------------
        # UPDATE PAYMENT
        # ---------------------------------------------

        payment.status = Payment.Status.REFUNDED

        payment.save(
            update_fields=[
                "status",
                "updated_at",
            ]
        )

        # ---------------------------------------------
        # UPDATE ORDER
        # ---------------------------------------------

        if order.status != Order.Status.CANCELLED:

            previous_status = order.status

            order.status = Order.Status.CANCELLED

            order.save(
                update_fields=[
                    "status",
                    "updated_at",
                ]
            )

            OrderStatusHistory.objects.create(
                order=order,
                previous_status=previous_status,
                new_status=order.status,
                changed_by=request.user,
            )

        # ---------------------------------------------
        # RESPONSE
        # ---------------------------------------------

        return Response(
            {
                "message": (
                    "Refund processed successfully."
                ),
                "refund": AdminRefundDetailSerializer(
                    refund
                ).data,
            },
            status=status.HTTP_200_OK,
        )


class AdminRefundListAPIView(generics.ListAPIView):
    permission_classes = (
        IsOrderManagementStaff,
    )

    serializer_class = AdminRefundListSerializer

    pagination_class = AdminListPagination

    filter_backends = (
        DjangoFilterBackend,
        filters.SearchFilter,
    )

    filterset_class = AdminRefundFilter

    search_fields = (
        "id",
        "payment__id",
        "payment__order__id",
        "payment__order__customer__first_name",
        "payment__order__customer__last_name",
        "payment__order__customer__email",
        "payment__order__customer__phone_number",
        "refund_reference",
    )

    def get_queryset(self):
        return (
            Refund.objects
            .select_related(
                "payment",
                "payment__order",
                "payment__order__customer",
                "processed_by",
            )
            .order_by("-created_at")
        )


class AdminRefundDetailAPIView(generics.RetrieveAPIView):
    permission_classes = (
        IsOrderManagementStaff,
    )

    serializer_class = AdminRefundDetailSerializer

    lookup_url_kwarg = "refund_id"

    def get_queryset(self):
        return (
            Refund.objects
            .select_related(
                "payment",
                "payment__order",
                "payment__order__customer",
                "processed_by",
            )
        )