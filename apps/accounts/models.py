from django.db import models

# Create your models here.
from django.contrib.auth.base_user import BaseUserManager
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
import secrets
from django.utils import timezone
from datetime import timedelta



class UserManager(BaseUserManager):
    """
    Custom manager for the User model.
    """

    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("The email address is required.")

        email = self.normalize_email(email)

        user = self.model(
            email=email,
            **extra_fields,
        )

        if password:
            user.set_password(password)
        else:
            user.set_unusable_password()

        user.save(using=self._db)

        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)
        extra_fields.setdefault("role", self.model.Role.ADMIN)

        if not password:
            raise ValueError("Superuser must have a password.")

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")

        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")

        return self.create_user(
            email=email,
            password=password,
            **extra_fields,
        )


from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.db import models


class User(AbstractBaseUser, PermissionsMixin):

    class Role(models.TextChoices):
        CUSTOMER = "CUSTOMER", "Customer"
        ADMIN = "ADMIN", "Admin"
        STAFF = "STAFF", "Staff"
        MANAGER = "MANAGER", "Manager"
        WAREHOUSE = "WAREHOUSE", "Warehouse"
        DELIVERY = "DELIVERY", "Delivery"

    email = models.EmailField(
        unique=True,
        db_index=True,
    )

    phone_number = models.CharField(
        max_length=15,
        unique=True,
        null=True,
        blank=True,
    )

    first_name = models.CharField(
        max_length=100,
    )

    last_name = models.CharField(
        max_length=100,
        blank=True,
    )

    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.CUSTOMER,
        db_index=True,
    )

    is_verified = models.BooleanField(
        default=False,
    )

    is_active = models.BooleanField(
        default=True,
    )

    is_staff = models.BooleanField(
        default=False,
    )

    date_joined = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    def __str__(self):
        return self.email


class Address(models.Model):

    class AddressType(models.TextChoices):
        HOME = "HOME", "Home"
        WORK = "WORK", "Work"
        OTHER = "OTHER", "Other"

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="addresses",
    )

    address_type = models.CharField(
        max_length=10,
        choices=AddressType.choices,
        default=AddressType.HOME,
    )

    full_name = models.CharField(
        max_length=150,
    )

    phone_number = models.CharField(
        max_length=15,
    )

    address_line_1 = models.CharField(
        max_length=255,
    )

    address_line_2 = models.CharField(
        max_length=255,
        blank=True,
    )

    landmark = models.CharField(
        max_length=255,
        blank=True,
    )

    city = models.CharField(
        max_length=100,
    )

    state = models.CharField(
        max_length=100,
    )

    pincode = models.CharField(
        max_length=10,
    )

    country = models.CharField(
        max_length=100,
        default="India",
    )

    is_default = models.BooleanField(
        default=False,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        ordering = ["-is_default", "-created_at"]

    def __str__(self):
        return f"{self.full_name} - {self.city}"


class PhoneVerificationOTP(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="phone_verification_otps",
    )

    phone_number = models.CharField(
        max_length=15,
    )

    otp_hash = models.CharField(
        max_length=128,
    )

    expires_at = models.DateTimeField()

    attempts = models.PositiveSmallIntegerField(
        default=0,
    )

    is_used = models.BooleanField(
        default=False,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    def is_expired(self):
        return timezone.now() >= self.expires_at

    def __str__(self):
        return f"Phone verification for {self.phone_number}"