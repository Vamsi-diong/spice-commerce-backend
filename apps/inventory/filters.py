from django.core.exceptions import ValidationError

from django_filters import rest_framework as filters

from .models import Order, Payment,Refund


class AdminOrderFilter(filters.FilterSet):

    customer_id = filters.NumberFilter(
        field_name="customer_id",
    )

    date_from = filters.DateFilter(
        field_name="created_at",
        lookup_expr="date__gte",
    )

    date_to = filters.DateFilter(
        field_name="created_at",
        lookup_expr="date__lte",
    )

    def clean(self):
        cleaned_data = super().clean()

        date_from = cleaned_data.get("date_from")
        date_to = cleaned_data.get("date_to")

        if date_from and date_to and date_from > date_to:
            raise ValidationError(
                "date_from cannot be later than date_to."
            )

        return cleaned_data

    class Meta:
        model = Order

        fields = (
            "status",
            "customer_id",
            "date_from",
            "date_to",
        )


class AdminPaymentFilter(filters.FilterSet):

    date_from = filters.DateFilter(
        field_name="created_at",
        lookup_expr="date__gte",
    )

    date_to = filters.DateFilter(
        field_name="created_at",
        lookup_expr="date__lte",
    )

    def clean(self):
        cleaned_data = super().clean()

        date_from = cleaned_data.get("date_from")
        date_to = cleaned_data.get("date_to")

        if date_from and date_to and date_from > date_to:
            raise ValidationError(
                "date_from cannot be later than date_to."
            )

        return cleaned_data

    class Meta:
        model = Payment

        fields = (
            "status",
            "method",
            "date_from",
            "date_to",
        )


class AdminRefundFilter(filters.FilterSet):

    date_from = filters.DateFilter(
        field_name="created_at",
        lookup_expr="date__gte",
    )

    date_to = filters.DateFilter(
        field_name="created_at",
        lookup_expr="date__lte",
    )

    def clean(self):
        cleaned_data = super().clean()

        date_from = cleaned_data.get("date_from")
        date_to = cleaned_data.get("date_to")

        if date_from and date_to and date_from > date_to:
            raise ValidationError(
                "date_from cannot be later than date_to."
            )

        return cleaned_data

    class Meta:
        model = Refund

        fields = (
            "status",
            "date_from",
            "date_to",
        )