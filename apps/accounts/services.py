import hashlib
import secrets
from datetime import timedelta

from decouple import config
from django.utils import timezone

from .models import PhoneVerificationOTP,EmailVerificationOTP


OTP_EXPIRY_MINUTES = 5
MAX_OTP_ATTEMPTS = 5


def generate_otp():
    """
    Generate OTP.

    Development:
        Uses static OTP from environment.

    Production:
        Generates a secure random 6-digit OTP.
    """

    otp_mode = config("OTP_MODE", default="static")

    if otp_mode == "static":
        return config("STATIC_OTP", default="123456")

    return f"{secrets.randbelow(1_000_000):06d}"


def hash_otp(otp):
    """
    Hash OTP before storing it in the database.
    """

    return hashlib.sha256(
        otp.encode("utf-8")
    ).hexdigest()


def create_otp(phone_number, purpose):
    """
    Create an OTP for a phone number and a specific purpose.

    Supported purposes:
        LOGIN
        PHONE_CHANGE
    """

    # Invalidate previous unused OTPs
    # for the same phone number and purpose.
    PhoneVerificationOTP.objects.filter(
        phone_number=phone_number,
        purpose=purpose,
        is_used=False,
    ).update(
        is_used=True,
    )

    otp = generate_otp()

    verification = PhoneVerificationOTP.objects.create(
        phone_number=phone_number,
        purpose=purpose,
        otp_hash=hash_otp(otp),
        expires_at=timezone.now()
        + timedelta(minutes=OTP_EXPIRY_MINUTES),
    )

    return verification, otp


def verify_otp(phone_number, otp, purpose):
    """
    Verify the latest valid OTP for a phone number
    and purpose.

    Returns:
        (True, message) on success
        (False, message) on failure
    """

    verification = (
        PhoneVerificationOTP.objects
        .filter(
            phone_number=phone_number,
            purpose=purpose,
            is_used=False,
        )
        .order_by("-created_at")
        .first()
    )

    if verification is None:
        return False, "Invalid OTP."

    if verification.is_expired():
        verification.is_used = True
        verification.save(update_fields=["is_used"])

        return False, "OTP has expired."

    if verification.attempts >= MAX_OTP_ATTEMPTS:
        verification.is_used = True
        verification.save(update_fields=["is_used"])

        return False, "Maximum OTP attempts exceeded."

    verification.attempts += 1
    verification.save(update_fields=["attempts"])

    if not secrets.compare_digest(
        verification.otp_hash,
        hash_otp(otp),
    ):
        return False, "Invalid OTP."

    verification.is_used = True
    verification.save(update_fields=["is_used"])

    return True, "OTP verified successfully."


def create_phone_verification_otp(user, phone_number):
    """
    Backward-compatible helper for the existing
    phone-change API.

    This will be used until we update the views.
    """

    return create_otp(
        phone_number=phone_number,
        purpose=PhoneVerificationOTP.Purpose.PHONE_CHANGE,
    )


def verify_phone_otp(user, phone_number, otp):
    """
    Backward-compatible helper for the existing
    phone-change API.

    After successful verification, update the user's
    phone number.
    """

    success, message = verify_otp(
        phone_number=phone_number,
        otp=otp,
        purpose=PhoneVerificationOTP.Purpose.PHONE_CHANGE,
    )

    if not success:
        return False, message

    user.phone_number = phone_number
    user.save(update_fields=["phone_number"])

    return True, "Phone number verified successfully."


def create_email_verification_otp(user, email):
    """
    Create an email verification OTP for an authenticated user.
    """

    EmailVerificationOTP.objects.filter(
        user=user,
        is_used=False,
    ).update(
        is_used=True,
    )

    otp = generate_otp()

    verification = EmailVerificationOTP.objects.create(
        user=user,
        email=email,
        otp_hash=hash_otp(otp),
        expires_at=timezone.now()
        + timedelta(minutes=OTP_EXPIRY_MINUTES),
    )

    return verification, otp


def verify_email_otp(user, email, otp):
    """
    Verify the latest valid email OTP.
    """

    verification = (
        EmailVerificationOTP.objects
        .filter(
            user=user,
            email=email,
            is_used=False,
        )
        .order_by("-created_at")
        .first()
    )

    if verification is None:
        return False, "Invalid OTP."

    if verification.is_expired():
        verification.is_used = True
        verification.save(update_fields=["is_used"])

        return False, "OTP has expired."

    if verification.attempts >= MAX_OTP_ATTEMPTS:
        verification.is_used = True
        verification.save(update_fields=["is_used"])

        return False, "Maximum OTP attempts exceeded."

    verification.attempts += 1
    verification.save(update_fields=["attempts"])

    if not secrets.compare_digest(
        verification.otp_hash,
        hash_otp(otp),
    ):
        return False, "Invalid OTP."

    verification.is_used = True
    verification.save(update_fields=["is_used"])

    user.email = email
    user.email_verified = True

    user.save(
        update_fields=[
            "email",
            "email_verified",
        ]
    )

    return True, "Email verified successfully."