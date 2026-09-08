from django.urls import path

from .views import (AddCartItemAPIView,CartAPIView,UpdateCartItemAPIView,CheckoutAPIView,OrderListAPIView, OrderDetailAPIView, CancelOrderAPIView, UpdateOrderStatusAPIView, AdminOrderListAPIView, AdminOrderDetailAPIView,CreatePaymentAPIView, PaymentSuccessAPIView, PaymentFailureAPIView,CollectCODPaymentAPIView,
AdminPaymentSuccessAPIView,AdminPaymentListAPIView,AdminPaymentDetailAPIView,AdminPaymentFailureAPIView,AdminOrderStatusHistoryAPIView,AdminRefundAPIView,AdminRefundListAPIView,AdminRefundDetailAPIView)

urlpatterns = [

    path("cart/items/",AddCartItemAPIView.as_view(),name="add-cart-item",),
    path("cart/",CartAPIView.as_view(),name="cart",),
    path("cart/items/<int:cart_item_id>/",UpdateCartItemAPIView.as_view(),name="update-cart-item",),
    path("checkout/",CheckoutAPIView.as_view(),name="checkout",),
    path("orders/",OrderListAPIView.as_view(),name="order-list",),
    path("orders/<int:id>/",OrderDetailAPIView.as_view(),name="order-detail",),
    path("orders/<int:id>/cancel/",CancelOrderAPIView.as_view(),name="cancel-order",),
    path("admin/orders/<int:id>/status/",UpdateOrderStatusAPIView.as_view(),name="update-order-status",),
    path("admin/orders/",AdminOrderListAPIView.as_view(),name="admin-order-list",),
    path("admin/orders/<int:id>/",AdminOrderDetailAPIView.as_view(),name="admin-order-detail",),
    path("payments/",CreatePaymentAPIView.as_view(),name="create-payment",),
    path("payments/<int:payment_id>/success/",PaymentSuccessAPIView.as_view(),name="payment-success",),
    path("payments/<int:payment_id>/failure/",PaymentFailureAPIView.as_view(),name="payment-failure",),
    path("admin/payments/<int:payment_id>/collect-cod/",CollectCODPaymentAPIView.as_view(),name="collect-cod-payment",),
    path("admin/payments/<int:payment_id>/success/",AdminPaymentSuccessAPIView.as_view(),name="admin-payment-success",),
    path("admin/payments/",AdminPaymentListAPIView.as_view(),name="admin-payment-list",),
    path("admin/payments/<int:payment_id>/",AdminPaymentDetailAPIView.as_view(),name="admin-payment-detail",),
    path("admin/payments/<int:payment_id>/failure/",AdminPaymentFailureAPIView.as_view(),name="admin-payment-failure",),
    path("admin/orders/<int:id>/history/",AdminOrderStatusHistoryAPIView.as_view(),name="admin-order-status-history",),
    path("admin/payments/<int:payment_id>/refund/",AdminRefundAPIView.as_view(),name="admin-payment-refund",),
    path("admin/refunds/",AdminRefundListAPIView.as_view(),name="admin-refund-list",),
    path("admin/refunds/<int:refund_id>/",AdminRefundDetailAPIView.as_view(),name="admin-refund-detail",),

]