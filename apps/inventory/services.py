from decimal import Decimal


def calculate_delivery_charge(distance_km):
    if distance_km < 80:
        return Decimal("0.00")

    if distance_km <= 110:
        return Decimal("10.00")

    if distance_km <= 150:
        return Decimal("20.00")

    return Decimal("50.00")