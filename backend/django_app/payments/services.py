import re

from django.utils import timezone


def clean_card_number(card_number):
    """
    Remove spaces and non-digit characters.
    """

    if not card_number:
        raise ValueError(
            "Card number is required."
        )

    return re.sub(
        r"\D",
        "",
        str(card_number),
    )


def validate_card_number(card_number):
    """
    Basic card number validation
    using length + Luhn algorithm.
    """

    card_number = clean_card_number(
        card_number
    )

    if not 13 <= len(card_number) <= 19:
        raise ValueError(
            "Card number must contain 13 to 19 digits."
        )

    digits = [
        int(digit)
        for digit in card_number
    ]

    checksum = 0
    parity = len(digits) % 2

    for index, digit in enumerate(digits):
        if index % 2 == parity:
            digit *= 2

            if digit > 9:
                digit -= 9

        checksum += digit

    if checksum % 10 != 0:
        raise ValueError(
            "Invalid card number."
        )

    return card_number


def detect_card_brand(card_number):
    """
    Detect common card brand.
    """

    if card_number.startswith("4"):
        return "VISA"

    first_two = int(
        card_number[:2]
    )

    first_four = int(
        card_number[:4]
    )

    if 51 <= first_two <= 55:
        return "MASTERCARD"

    if 2221 <= first_four <= 2720:
        return "MASTERCARD"

    if (
        card_number.startswith("34")
        or card_number.startswith("37")
    ):
        return "AMEX"

    if (
        card_number.startswith("6011")
        or card_number.startswith("65")
    ):
        return "DISCOVER"

    return "UNKNOWN"


def create_masked_card_number(
    card_number,
):
    """
    Store only masked number.
    """

    return (
        "*" * (len(card_number) - 4)
        + card_number[-4:]
    )


def validate_cvv(cvv):
    """
    CVV is validated but never stored.
    """

    if not cvv:
        raise ValueError(
            "CVV is required."
        )

    cvv = str(cvv).strip()

    if not cvv.isdigit():
        raise ValueError(
            "CVV must contain digits only."
        )

    if len(cvv) not in (3, 4):
        raise ValueError(
            "CVV must contain 3 or 4 digits."
        )

    return True


def validate_expiry(
    expiry_month,
    expiry_year,
):
    """
    Validate card expiry date.
    """

    if not 1 <= int(expiry_month) <= 12:
        raise ValueError(
            "Expiry month must be between 1 and 12."
        )

    now = timezone.now()

    current_year = now.year
    current_month = now.month

    expiry_month = int(expiry_month)
    expiry_year = int(expiry_year)

    if expiry_year < current_year:
        raise ValueError(
            "Card has expired."
        )

    if (
        expiry_year == current_year
        and expiry_month < current_month
    ):
        raise ValueError(
            "Card has expired."
        )

    return True