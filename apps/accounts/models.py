from django.db import models

# Create your models here.
from django.contrib.auth.base_user import BaseUserManager
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.utils import timezone



class UserManager(BaseUserManager):
    """
    Custom manager for the User model.
    """

    def create_user(self, phone_number, email=None, password=None, **extra_fields):
        if not phone_number:
            raise ValueError("The phone number is required.")

        user = self.model(
            phone_number=phone_number,
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
        if not email:
            raise ValueError("Superuser must have an email.")

        if not password:
            raise ValueError("Superuser must have a password.")

        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)
        extra_fields.setdefault("role", self.model.Role.ADMIN)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")

        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")

        user = self.model(
            email=email,
            **extra_fields,
        )

        user.set_password(password)
        user.save(using=self._db)

        return user


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
        null=True,
        blank=True,
        db_index=True,
    )
    email_verified = models.BooleanField(
        default=False,
    )

    phone_number = models.CharField(
        max_length=15,
        unique=True,
        null=True,
        blank=True,
        db_index=True,
    )

    first_name = models.CharField(
        max_length=100,
        blank=True,
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

    is_verified = models.BooleanField(default=False)

    profile_completed = models.BooleanField(default=False)

    is_active = models.BooleanField(default=True)

    is_staff = models.BooleanField(default=False)

    date_joined = models.DateTimeField(auto_now_add=True)

    updated_at = models.DateTimeField(auto_now=True)

    objects = UserManager()

    USERNAME_FIELD = "phone_number"
    REQUIRED_FIELDS = []

    def __str__(self):
        return self.phone_number or self.email or f"User {self.id}"


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

    class Purpose(models.TextChoices):
        LOGIN = "LOGIN", "Login"
        PHONE_CHANGE = "PHONE_CHANGE", "Phone Change"       

    phone_number = models.CharField(
        max_length=15,
        db_index=True,
    )

    purpose = models.CharField(
        max_length=30,
        choices=Purpose.choices,
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
        return f"{self.phone_number} - {self.purpose}"


class EmailVerificationOTP(models.Model):

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="email_verification_otps",
    )

    email = models.EmailField(
        db_index=True,
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
        return f"{self.email} - Email Verification"