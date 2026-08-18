from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from rest_framework_simplejwt.views import TokenRefreshView

from .views import RegisterAPIView,LoginAPIView,MeAPIView,LogoutAPIView,AddressDetailAPIView,AddressListCreateAPIView,LoginAPIView,LogoutAPIView,PhoneChangeAPIView,PhoneVerifyAPIView,RequestOTPAPIView,VerifyLoginOTPAPIView,AddEmailAPIView,VerifyEmailAPIView



urlpatterns = [

    path("token/refresh/",TokenRefreshView.as_view(),name="token_refresh",),
    path("register/",RegisterAPIView.as_view(),name="register",),
    path("login/",LoginAPIView.as_view(),name="login",),
    path("me/",MeAPIView.as_view(),name="me",),
    path("logout/",LogoutAPIView.as_view(),name="logout",),
    path("addresses/",AddressListCreateAPIView.as_view(),name="address-list-create",),
    path("addresses/<int:pk>/",AddressDetailAPIView.as_view(),name="address-detail",),
    path("phone/change/",PhoneChangeAPIView.as_view(),name="phone-change",),
    path("phone/verify/",PhoneVerifyAPIView.as_view(),name="phone-verify",),
    path("auth/request-otp/",RequestOTPAPIView.as_view(),name="request-login-otp",),
    path("auth/verify-otp/",VerifyLoginOTPAPIView.as_view(),name="verify-login-otp",),
    path("email/request-verification/",AddEmailAPIView.as_view(),name="email/request-verification/",),
    path("email/verify/",VerifyEmailAPIView.as_view(),name="email-verify",),

]
