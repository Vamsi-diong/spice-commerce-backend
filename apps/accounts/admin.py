from django import forms
from django.contrib import admin
from django.contrib.auth.forms import ReadOnlyPasswordHashField

from .models import (
    User,
    Address,
    PhoneVerificationOTP,
    EmailVerificationOTP,
)


# ============================================================
# USER FORMS
# ============================================================

class UserCreationForm(forms.ModelForm):
    """
    Form used by Django Admin to create users.
    """

    password1 = forms.CharField(
        label="Password",
        widget=forms.PasswordInput,
        required=False,
    )

    password2 = forms.CharField(
        label="Confirm Password",
        widget=forms.PasswordInput,
        required=False,
    )

    class Meta:
        model = User
        fields = (
            "email",
            "phone_number",
            "first_name",
            "last_name",
            "role",
            "is_verified",
            "email_verified",
            "profile_completed",
            "is_active",
            "is_staff",
            "is_superuser",
        )

    def clean(self):
        cleaned_data = super().clean()

        password1 = cleaned_data.get("password1")
        password2 = cleaned_data.get("password2")

        if password1 or password2:
            if password1 != password2:
                raise forms.ValidationError(
                    "Passwords do not match."
                )

        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)

        password = self.cleaned_data.get("password1")

        if password:
            user.set_password(password)
        else:
            user.set_unusable_password()

        if commit:
            user.save()

        return user


class UserChangeForm(forms.ModelForm):
    """
    Form used by Django Admin to edit existing users.
    """

    password = ReadOnlyPasswordHashField(
        label="Password",
        help_text=(
            "Passwords are stored as hashes and cannot be viewed. "
            "Use the password change form to change the password."
        ),
    )

    class Meta:
        model = User
        fields = (
            "email",
            "phone_number",
            "password",
            "first_name",
            "last_name",
            "role",
            "is_verified",
            "email_verified",
            "profile_completed",
            "is_active",
            "is_staff",
            "is_superuser",
            "groups",
            "user_permissions",
        )


# ============================================================
# USER ADMIN
# ============================================================

@admin.register(User)
class UserAdmin(admin.ModelAdmin):

    form = UserChangeForm
    add_form = UserCreationForm

    list_display = (
        "id",
        "email",
        "phone_number",
        "first_name",
        "last_name",
        "role",
        "is_verified",
        "email_verified",
        "profile_completed",
        "is_active",
        "is_staff",
        "is_superuser",
        "date_joined",
    )

    list_filter = (
        "role",
        "is_verified",
        "email_verified",
        "profile_completed",
        "is_active",
        "is_staff",
        "is_superuser",
    )

    search_fields = (
        "email",
        "phone_number",
        "first_name",
        "last_name",
    )

    ordering = (
        "-date_joined",
    )

    readonly_fields = (
        "date_joined",
        "updated_at",
        "last_login",
    )

    fieldsets = (
        (
            "Account Information",
            {
                "fields": (
                    "email",
                    "phone_number",
                    "password",
                )
            },
        ),
        (
            "Personal Information",
            {
                "fields": (
                    "first_name",
                    "last_name",
                )
            },
        ),
        (
            "Role & Verification",
            {
                "fields": (
                    "role",
                    "is_verified",
                    "email_verified",
                    "profile_completed",
                )
            },
        ),
        (
            "Permissions",
            {
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                )
            },
        ),
        (
            "Important Dates",
            {
                "fields": (
                    "last_login",
                    "date_joined",
                    "updated_at",
                )
            },
        ),
    )

    add_fieldsets = (
        (
            "Account Information",
            {
                "classes": ("wide",),
                "fields": (
                    "email",
                    "phone_number",
                    "password1",
                    "password2",
                ),
            },
        ),
        (
            "Personal Information",
            {
                "fields": (
                    "first_name",
                    "last_name",
                )
            },
        ),
        (
            "Role & Verification",
            {
                "fields": (
                    "role",
                    "is_verified",
                    "email_verified",
                    "profile_completed",
                )
            },
        ),
        (
            "Permissions",
            {
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_superuser",
                )
            },
        ),
    )

    def get_form(self, request, obj=None, **kwargs):
        """
        Use the creation form when adding a new user,
        otherwise use the change form.
        """
        defaults = {}

        if obj is None:
            defaults["form"] = self.add_form
        else:
            defaults["form"] = self.form

        defaults.update(kwargs)

        return super().get_form(
            request,
            obj,
            **defaults,
        )


# ============================================================
# ADDRESS ADMIN
# ============================================================

@admin.register(Address)
class AddressAdmin(admin.ModelAdmin):

    list_display = (
        "id",
        "full_name",
        "user",
        "address_type",
        "phone_number",
        "city",
        "state",
        "pincode",
        "country",
        "is_default",
        "created_at",
    )

    list_filter = (
        "address_type",
        "state",
        "city",
        "country",
        "is_default",
    )

    search_fields = (
        "full_name",
        "phone_number",
        "city",
        "state",
        "pincode",
        "user__email",
        "user__phone_number",
    )

    ordering = (
        "-created_at",
    )

    readonly_fields = (
        "created_at",
        "updated_at",
    )


# ============================================================
# PHONE OTP ADMIN
# ============================================================

@admin.register(PhoneVerificationOTP)
class PhoneVerificationOTPAdmin(admin.ModelAdmin):

    list_display = (
        "id",
        "phone_number",
        "purpose",
        "attempts",
        "is_used",
        "expires_at",
        "created_at",
    )

    list_filter = (
        "purpose",
        "is_used",
    )

    search_fields = (
        "phone_number",
    )

    ordering = (
        "-created_at",
    )

    readonly_fields = (
        "otp_hash",
        "created_at",
    )


# ============================================================
# EMAIL OTP ADMIN
# ============================================================

@admin.register(EmailVerificationOTP)
class EmailVerificationOTPAdmin(admin.ModelAdmin):

    list_display = (
        "id",
        "user",
        "email",
        "attempts",
        "is_used",
        "expires_at",
        "created_at",
    )

    list_filter = (
        "is_used",
    )

    search_fields = (
        "email",
        "user__email",
        "user__phone_number",
    )

    ordering = (
        "-created_at",
    )

    readonly_fields = (
        "otp_hash",
        "created_at",
    )