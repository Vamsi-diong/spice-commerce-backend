from django.shortcuts import render

# Create your views here.
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from .services import create_phone_verification_otp,verify_phone_otp
from apps.accounts.models import Address

from .serializers import RegisterSerializer,LoginSerializer,UserSerializer,LogoutSerializer,AddressSerializer,PhoneChangeSerializer,PhoneVerifySerializer
from rest_framework.generics import (
    ListCreateAPIView,
    RetrieveUpdateDestroyAPIView,
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
        serializer.save(user=self.request.user)

class AddressDetailAPIView(RetrieveUpdateDestroyAPIView):
    serializer_class = AddressSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Address.objects.filter(
            user=self.request.user
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