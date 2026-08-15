from django.urls import path

from .views import RegisterAPIView,LoginAPIView,MeAPIView,LogoutAPIView
from rest_framework_simplejwt.views import TokenRefreshView


urlpatterns = [

    path("token/refresh/",TokenRefreshView.as_view(),name="token_refresh",),

    path("register/",RegisterAPIView.as_view(),name="register",),
    path("login/",LoginAPIView.as_view(),name="login",),
    path("me/",MeAPIView.as_view(),name="me",),
    path("logout/",LogoutAPIView.as_view(),name="logout",),

]
