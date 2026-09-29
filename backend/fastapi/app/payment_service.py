import random

from .config import settings


def simulate_payment():
    """
    Simulate payment success/failure.

    Returns:
        ("SUCCESS", "")
    or
        ("FAILED", "Simulated payment failure.")
    """

    random_value = random.randint(
        1,
        100,
    )

    if random_value <= settings.PAYMENT_SUCCESS_RATE:
        return (
            "SUCCESS",
            "",
        )

    return (
        "FAILED",
        "Simulated payment failure.",
    )