import hashlib
import secrets
from datetime import timedelta

from django.utils import timezone

from .models import PhoneVerificationOTP


OTP_EXPIRY_MINUTES = 5
MAX_OTP_ATTEMPTS = 5


def generate_otp():
    """
    Generate a secure 6-digit OTP.
    """
    return f"{secrets.randbelow(1_000_000):06d}"


def hash_otp(otp):
    """
    Hash OTP before storing it in the database.
    """
    return hashlib.sha256(
        otp.encode("utf-8")
    ).hexdigest()


def create_phone_verification_otp(user, phone_number):
    """
    Create a new phone verification OTP.
    """

    # Invalidate previous unused OTPs for this phone number.
    PhoneVerificationOTP.objects.filter(
        user=user,
        phone_number=phone_number,
        is_used=False,
    ).update(
        is_used=True,
    )

    otp = generate_otp()

    verification = PhoneVerificationOTP.objects.create(
        user=user,
        phone_number=phone_number,
        otp_hash=hash_otp(otp),
        expires_at=timezone.now()
        + timedelta(minutes=OTP_EXPIRY_MINUTES),
    )

    return verification, otp


def verify_phone_otp(user, phone_number, otp):
    """
    Verify the latest valid OTP for a phone number.
    """

    verification = (
        PhoneVerificationOTP.objects
        .filter(
            user=user,
            phone_number=phone_number,
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

    user.phone_number = phone_number
    user.save(update_fields=["phone_number"])

    return True, "Phone number verified successfully."