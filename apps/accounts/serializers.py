from django.contrib.auth import authenticate, get_user_model
from .models import Address
from rest_framework import serializers
from rest_framework_simplejwt.tokens import RefreshToken

User = get_user_model()


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(
        write_only=True,
        min_length=8,
    )

    password_confirm = serializers.CharField(
        write_only=True,
    )

    class Meta:
        model = User
        fields = (
            "email",
            "password",
            "password_confirm",
            "first_name",
            "last_name",
            "phone_number",
        )

    def validate(self, attrs):
        if attrs["password"] != attrs["password_confirm"]:
            raise serializers.ValidationError(
                {"password": "Passwords do not match."}
            )

        return attrs

    def create(self, validated_data):
        validated_data.pop("password_confirm")

        password = validated_data.pop("password")

        user = User.objects.create_user(
            password=password,
            role=User.Role.CUSTOMER,
            **validated_data,
        )

        return user



User = get_user_model()
class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(
        write_only=True,
    )

    def validate(self, attrs):
        email = attrs["email"]
        password = attrs["password"]

        user = authenticate(
            request=self.context.get("request"),
            username=email,
            password=password,
        )

        if user is None:
            raise serializers.ValidationError(
                "Invalid email or password."
            )

        if not user.is_active:
            raise serializers.ValidationError(
                "This account is inactive."
            )

        refresh = RefreshToken.for_user(user)

        attrs["user"] = user
        attrs["refresh"] = str(refresh)
        attrs["access"] = str(refresh.access_token)

        return attrs


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = (
            "id",
            "email",
            "phone_number",
            "first_name",
            "last_name",
            "role",
            "is_verified",
            "profile_completed",
            "date_joined",
        )

        read_only_fields = (
            "id",
            "phone_number",
            "role",
            "is_verified",
            "profile_completed",
            "date_joined",
        )

    def validate_email(self, value):
        user = self.instance

        if User.objects.filter(
            email=value
        ).exclude(
            id=user.id
        ).exists():
            raise serializers.ValidationError(
                "This email is already registered."
            )

        return value

    def update(self, instance, validated_data):
        user = super().update(
            instance,
            validated_data,
        )

        self.update_profile_completion(user)

        return user

    @staticmethod
    def update_profile_completion(user):
        has_basic_details = all(
            [
                user.first_name.strip(),
                user.last_name.strip(),
                user.email,
            ]
        )

        has_address = user.addresses.exists()

        user.profile_completed = (
            has_basic_details
            and has_address
        )

        user.save(
            update_fields=["profile_completed"]
        )


class LogoutSerializer(serializers.Serializer):
    refresh = serializers.CharField()

    def validate(self, attrs):
        self.token = attrs["refresh"]
        return attrs

    def save(self, **kwargs):
        try:
            token = RefreshToken(self.token)
            token.blacklist()
        except Exception:
            raise serializers.ValidationError(
                {"refresh": "Invalid or already blacklisted refresh token."}
            )


class AddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = Address
        fields = (
            "id",
            "address_type",
            "full_name",
            "phone_number",
            "address_line_1",
            "address_line_2",
            "landmark",
            "city",
            "state",
            "pincode",
            "country",
            "is_default",
            "created_at",
            "updated_at",
        )
        read_only_fields = (
            "id",
            "created_at",
            "updated_at",
        )


class PhoneChangeSerializer(serializers.Serializer):
    phone_number = serializers.CharField(max_length=15)

    def validate_phone_number(self, value):
        user = self.context["request"].user

        if User.objects.filter(phone_number=value).exclude(
            id=user.id
        ).exists():
            raise serializers.ValidationError(
                "This phone number is already registered."
            )

        return value

class PhoneVerifySerializer(serializers.Serializer):
    phone_number = serializers.CharField(max_length=15)
    otp = serializers.CharField(
        min_length=6,
        max_length=6,
    )


class RequestOTPSerializer(serializers.Serializer):
    phone_number = serializers.CharField(
        max_length=15,
    )

    def validate_phone_number(self, value):
        value = value.strip()

        if not value.isdigit():
            raise serializers.ValidationError(
                "Phone number must contain only digits."
            )

        if len(value) < 10 or len(value) > 15:
            raise serializers.ValidationError(
                "Enter a valid phone number."
            )

        return value


class VerifyLoginOTPSerializer(serializers.Serializer):
    phone_number = serializers.CharField(
        max_length=15,
    )

    otp = serializers.CharField(
        min_length=6,
        max_length=6,
    )

    def validate_phone_number(self, value):
        value = value.strip()

        if not value.isdigit():
            raise serializers.ValidationError(
                "Phone number must contain only digits."
            )

        if len(value) < 10 or len(value) > 15:
            raise serializers.ValidationError(
                "Enter a valid phone number."
            )

        return value

    def validate_otp(self, value):
        if not value.isdigit():
            raise serializers.ValidationError(
                "OTP must contain only digits."
            )

        return value


class AddEmailSerializer(serializers.Serializer):
    email = serializers.EmailField()

    def validate_email(self, value):
        user = self.context["request"].user

        if User.objects.filter(
            email=value
        ).exclude(
            id=user.id
        ).exists():
            raise serializers.ValidationError(
                "This email is already registered."
            )

        if (
            user.email == value
            and user.email_verified
        ):
            raise serializers.ValidationError(
                "This email is already verified."
            )

        return value

class VerifyEmailSerializer(serializers.Serializer):
    email = serializers.EmailField()

    otp = serializers.CharField(
        min_length=6,
        max_length=6,
    )

    def validate_otp(self, value):
        if not value.isdigit():
            raise serializers.ValidationError(
                "OTP must contain only digits."
            )

        return value