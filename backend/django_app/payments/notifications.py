import logging

from django.conf import settings
from django.core.mail import send_mail


logger = logging.getLogger(__name__)


# =========================================================
# HELPER FUNCTIONS
# =========================================================


def _get_card_display(card):
    """
    Return a safe masked card value for emails.

    Only masked card information is used.
    """

    masked_number = getattr(
        card,
        "masked_number",
        "",
    )

    if masked_number:
        return masked_number

    last4 = getattr(
        card,
        "last4",
        "",
    )

    if last4:
        return f"****{last4}"

    return "Card"


def _send_notification_email(
    recipient,
    subject,
    message,
):
    """
    Send a notification email.

    Returns True when the email is sent successfully.
    Returns False when notifications are disabled,
    recipient is missing, or sending fails.

    Email failures must never break the main
    payment/card management workflow.
    """

    if not getattr(
        settings,
        "EMAIL_NOTIFICATIONS_ENABLED",
        False,
    ):
        return False

    if not recipient:
        return False

    try:
        send_mail(
            subject=subject,
            message=message,
            from_email=getattr(
                settings,
                "DEFAULT_FROM_EMAIL",
                None,
            ),
            recipient_list=[
                recipient
            ],
            fail_silently=False,
        )

        return True

    except Exception:
        logger.exception(
            "Email notification failed."
        )

        return False


# =========================================================
# CARD BLOCKED ALERT
# =========================================================


def send_card_blocked_alert(card):
    """
    Send an alert when an administrator blocks a card.
    """

    user = getattr(
        card,
        "user",
        None,
    )

    recipient = getattr(
        user,
        "email",
        "",
    )

    card_display = _get_card_display(
        card
    )

    subject = (
        "CreditPay - Card Blocked Alert"
    )

    message = (
        "Hello,\n\n"
        "Your CreditPay card has been blocked.\n\n"
        f"Card: {card_display}\n"
        f"Card Brand: {card.card_brand}\n"
        f"Card Type: {card.card_type}\n\n"
        "You will not be able to use this card "
        "for new transactions while it is blocked.\n\n"
        "Please contact the administrator or "
        "support team if you believe this action "
        "was made in error.\n\n"
        "Regards,\n"
        "CreditPay"
    )

    return _send_notification_email(
        recipient=recipient,
        subject=subject,
        message=message,
    )


# =========================================================
# LOW CREDIT ALERT
# =========================================================


def send_low_credit_alert(
    card,
    available_credit,
):
    """
    Send an alert when available credit falls
    below 10 percent of the credit limit.
    """

    user = getattr(
        card,
        "user",
        None,
    )

    recipient = getattr(
        user,
        "email",
        "",
    )

    card_display = _get_card_display(
        card
    )

    credit_limit = card.credit_limit

    if credit_limit:
        available_percentage = (
            (
                available_credit
                / credit_limit
            )
            * 100
        )
    else:
        available_percentage = 0

    subject = (
        "CreditPay - Low Available Credit Alert"
    )

    message = (
        "Hello,\n\n"
        "Your available credit has fallen "
        "below 10% of your credit limit.\n\n"
        f"Card: {card_display}\n"
        f"Card Brand: {card.card_brand}\n"
        f"Available Credit: "
        f"INR {available_credit:,.2f}\n"
        f"Credit Limit: "
        f"INR {credit_limit:,.2f}\n"
        f"Available Credit Percentage: "
        f"{available_percentage:.2f}%\n\n"
        "Please review your recent spending "
        "and available credit before making "
        "additional transactions.\n\n"
        "Regards,\n"
        "CreditPay"
    )

    return _send_notification_email(
        recipient=recipient,
        subject=subject,
        message=message,
    )