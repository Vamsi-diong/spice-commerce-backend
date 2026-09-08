from django.shortcuts import render

# Create your views here.
from rest_framework import status
from rest_framework import generics
from rest_framework import permissions
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from .services import create_phone_verification_otp,verify_phone_otp,create_otp,verify_otp,create_email_verification_otp,verify_email_otp
from apps.accounts.models import Address,PhoneVerificationOTP,PhoneVerificationOTP

from .serializers import RegisterSerializer,LoginSerializer,UserSerializer,LogoutSerializer,AddressSerializer,PhoneChangeSerializer,PhoneVerifySerializer,RequestOTPSerializer,VerifyLoginOTPSerializer,AddEmailSerializer,VerifyEmailSerializer
from rest_framework.generics import (
    ListCreateAPIView,
    RetrieveUpdateDestroyAPIView,
)
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import RefreshToken
User = get_user_model()

class RequestOTPAPIView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RequestOTPSerializer(
            data=request.data
        )

        serializer.is_valid(raise_exception=True)

        phone_number = serializer.validated_data["phone_number"]

        user_exists = User.objects.filter(
            phone_number=phone_number
        ).exists()

        verification, otp = create_otp(
            phone_number=phone_number,
            purpose=PhoneVerificationOTP.Purpose.LOGIN,
        )

        response_data = {
            "message": "OTP generated successfully.",
            "phone_number": phone_number,
            "expires_in": 300,
            "is_existing_user": user_exists,
        }

        # Development only
        response_data["otp"] = otp

        return Response(
            response_data,
            status=status.HTTP_200_OK,
        )


class VerifyLoginOTPAPIView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = VerifyLoginOTPSerializer(
            data=request.data
        )

        serializer.is_valid(raise_exception=True)

        phone_number = serializer.validated_data["phone_number"]
        otp = serializer.validated_data["otp"]

        success, message = verify_otp(
            phone_number=phone_number,
            otp=otp,
            purpose=PhoneVerificationOTP.Purpose.LOGIN,
        )

        if not success:
            return Response(
                {
                    "message": message,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        user = User.objects.filter(
            phone_number=phone_number
        ).first()

        is_new_user = False

        if user is None:
            user = User.objects.create_user(
                phone_number=phone_number,
                role=User.Role.CUSTOMER,
                is_verified=True,
            )

            is_new_user = True

        else:
            if not user.is_active:
                return Response(
                    {
                        "message": "This account is inactive."
                    },
                    status=status.HTTP_403_FORBIDDEN,
                )

            user.is_verified = True
            user.save(update_fields=["is_verified"])

        refresh = RefreshToken.for_user(user)

        return Response(
            {
                "message": "Login successful.",
                "is_new_user": is_new_user,
                "access": str(refresh.access_token),
                "refresh": str(refresh),
                "user": {
                    "id": user.id,
                    "phone_number": user.phone_number,
                    "email": user.email,
                    "first_name": user.first_name,
                    "last_name": user.last_name,
                    "role": user.role,
                    "is_verified": user.is_verified,
                    "profile_completed": user.profile_completed,
                },
            },
            status=status.HTTP_200_OK,
        )


class RegisterAPIView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = serializer.save()

        return Response(
            {
                "message": "Registration successful.",
                "user": {
                    "id": user.id,
                    "email": user.email,
                    "first_name": user.first_name,
                    "last_name": user.last_name,
                    "role": user.role,
                    "is_verified": user.is_verified,
                },
            },
            status=status.HTTP_201_CREATED,
        )


class LoginAPIView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = LoginSerializer(
            data=request.data,
            context={"request": request},
        )

        serializer.is_valid(raise_exception=True)

        user = serializer.validated_data["user"]

        return Response(
            {
                "message": "Login successful.",
                "access": serializer.validated_data["access"],
                "refresh": serializer.validated_data["refresh"],
                "user": {
                    "id": user.id,
                    "email": user.email,
                    "first_name": user.first_name,
                    "last_name": user.last_name,
                    "role": user.role,
                },
            },
            status=status.HTTP_200_OK,
        )



class MeAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = UserSerializer(request.user)

        return Response(
            serializer.data,
            status=status.HTTP_200_OK,
        )

    def patch(self, request):
        serializer = UserSerializer(
            request.user,
            data=request.data,
            partial=True,
        )

        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(
            serializer.data,
            status=status.HTTP_200_OK,
        )


class LogoutAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = LogoutSerializer(data=request.data)

        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(
            {
                "message": "Logout successful."
            },
            status=status.HTTP_200_OK,
        )


class AddressListCreateAPIView(ListCreateAPIView):
    serializer_class = AddressSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Address.objects.filter(
            user=self.request.user
        )

    def perform_create(self, serializer):
        user = self.request.user

        has_existing_addresses = user.addresses.exists()

        is_default = serializer.validated_data.get(
            "is_default",
            False,
        )

        if not has_existing_addresses:
            is_default = True

        if is_default:
            user.addresses.filter(
                is_default=True,
            ).update(
                is_default=False,
            )

        serializer.save(
            user=user,
            is_default=is_default,
        )

        if (
            user.first_name.strip()
            and user.last_name.strip()
            and user.email
            and user.addresses.exists()
        ):
            user.profile_completed = True
            user.save(
                update_fields=["profile_completed"]
            )

class AddressDetailAPIView(
    generics.RetrieveUpdateDestroyAPIView
):
    serializer_class = AddressSerializer
    permission_classes = (
        permissions.IsAuthenticated,
    )

    def get_queryset(self):
        return Address.objects.filter(
            user=self.request.user,
        )

    def perform_update(self, serializer):
        user = self.request.user

        is_default = serializer.validated_data.get(
            "is_default",
            None,
        )

        if is_default is True:
            user.addresses.filter(
                is_default=True,
            ).exclude(
                id=serializer.instance.id,
            ).update(
                is_default=False,
            )

        serializer.save()

    def perform_destroy(self, instance):
        user = self.request.user
        was_default = instance.is_default

        instance.delete()

        if was_default:
            new_default = user.addresses.order_by(
                "-created_at",
            ).first()

            if new_default:
                new_default.is_default = True
                new_default.save(
                    update_fields=["is_default"],
                )


class PhoneChangeAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = PhoneChangeSerializer(
            data=request.data,
            context={"request": request},
        )

        serializer.is_valid(raise_exception=True)

        phone_number = serializer.validated_data["phone_number"]

        verification, otp = create_phone_verification_otp(
            user=request.user,
            phone_number=phone_number,
        )

        return Response(
            {
                "message": "OTP generated successfully.",
                "phone_number": phone_number,
                "expires_in": 300,
                "otp": otp,
            },
            status=status.HTTP_200_OK,
        )

class PhoneVerifyAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = PhoneVerifySerializer(
            data=request.data,
        )

        serializer.is_valid(raise_exception=True)

        phone_number = serializer.validated_data["phone_number"]
        otp = serializer.validated_data["otp"]

        success, message = verify_phone_otp(
            user=request.user,
            phone_number=phone_number,
            otp=otp,
        )

        if not success:
            return Response(
                {
                    "message": message,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(
            {
                "message": message,
                "phone_number": phone_number,
            },
            status=status.HTTP_200_OK,
        )

class AddEmailAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = AddEmailSerializer(
            data=request.data,
            context={"request": request},
        )

        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data["email"]

        verification, otp = create_email_verification_otp(
            user=request.user,
            email=email,
        )

        return Response(
            {
                "message": "Email OTP generated successfully.",
                "email": email,
                "expires_in": 300,
                "otp": otp,
            },
            status=status.HTTP_200_OK,
        )

class VerifyEmailAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = VerifyEmailSerializer(
            data=request.data,
        )

        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data["email"]
        otp = serializer.validated_data["otp"]

        success, message = verify_email_otp(
            user=request.user,
            email=email,
            otp=otp,
        )

        if not success:
            return Response(
                {
                    "message": message,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(
            {
                "message": message,
                "email": email,
                "email_verified": True,
            },
            status=status.HTTP_200_OK,
        )