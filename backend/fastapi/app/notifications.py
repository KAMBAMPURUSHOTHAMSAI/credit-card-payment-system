
import logging
import smtplib
import ssl
from email.message import EmailMessage

from .config import settings


logger = logging.getLogger(__name__)


# =========================================================
# HELPER FUNCTION
# =========================================================

def _send_notification_email(
    recipient: str,
    subject: str,
    message: str,
) -> bool:
    """
    Send an email using the configured SMTP server.

    Returns True when sent successfully; otherwise False.
    Email failures must never break the payment flow.
    """

    if not settings.EMAIL_NOTIFICATIONS_ENABLED:
        return False

    if not recipient:
        return False

    if not settings.SMTP_HOST:
        logger.warning(
            "Email notification skipped: SMTP host is not configured."
        )
        return False

    if not settings.SMTP_FROM_EMAIL:
        logger.warning(
            "Email notification skipped: sender email is not configured."
        )
        return False

    try:
        email = EmailMessage()
        email["From"] = settings.SMTP_FROM_EMAIL
        email["To"] = recipient
        email["Subject"] = subject
        email.set_content(message)

        if settings.SMTP_USE_SSL:
            context = ssl.create_default_context()

            with smtplib.SMTP_SSL(
                settings.SMTP_HOST,
                settings.SMTP_PORT,
                context=context,
                timeout=15,
            ) as server:

                if settings.SMTP_USERNAME:
                    server.login(
                        settings.SMTP_USERNAME,
                        settings.SMTP_PASSWORD,
                    )

                server.send_message(email)

        else:
            with smtplib.SMTP(
                settings.SMTP_HOST,
                settings.SMTP_PORT,
                timeout=15,
            ) as server:

                server.ehlo()

                if settings.SMTP_USE_TLS:
                    context = ssl.create_default_context()
                    server.starttls(context=context)
                    server.ehlo()

                if settings.SMTP_USERNAME:
                    server.login(
                        settings.SMTP_USERNAME,
                        settings.SMTP_PASSWORD,
                    )

                server.send_message(email)

        return True

    except Exception:
        logger.exception("Email notification failed.")
        return False


# =========================================================
# HIGH VALUE TRANSACTION ALERT
# =========================================================

def send_high_value_transaction_alert(
    recipient: str,
    amount,
    card_display: str,
    reference: str,
) -> bool:
    """Alert the user about a successful transaction above INR 5,000."""

    subject = "CreditPay - High Value Transaction Alert"

    message = (
        "Hello,\n\n"
        "A high-value transaction was successfully "
        "processed on your CreditPay card.\n\n"
        f"Amount: INR {amount:,.2f}\n"
        f"Card: {card_display}\n"
        f"Reference: {reference}\n\n"
        "This alert was generated because the transaction "
        "amount is greater than INR 5,000.\n\n"
        "If you do not recognize this transaction, "
        "please contact the support team immediately.\n\n"
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
    recipient: str,
    available_credit,
    credit_limit,
    card_display: str,
) -> bool:
    """Alert the user when available credit falls below 10%."""

    if credit_limit:
        available_percentage = (
            available_credit / credit_limit
        ) * 100
    else:
        available_percentage = 0

    subject = "CreditPay - Low Available Credit Alert"

    message = (
        "Hello,\n\n"
        "Your available credit has fallen "
        "below 10% of your credit limit.\n\n"
        f"Card: {card_display}\n"
        f"Available Credit: INR {available_credit:,.2f}\n"
        f"Credit Limit: INR {credit_limit:,.2f}\n"
        f"Available Credit Percentage: {available_percentage:.2f}%\n\n"
        "Please review your recent spending "
        "before making additional transactions.\n\n"
        "Regards,\n"
        "CreditPay"
    )

    return _send_notification_email(
        recipient=recipient,
        subject=subject,
        message=message,
    )


# =========================================================
# FRAUD DETECTION ALERT
# =========================================================

def send_fraud_alert(
    recipient: str,
    card_display: str,
    amount,
    reference: str,
    payment_status: str,
    rule_details: str,
    ip_address: str = "",
) -> bool:
    """
    Alert the user when a transaction is flagged by
    the rule-based fraud detection service.
    """

    subject = "CreditPay - Suspicious Transaction Alert"

    message = (
        "Hello,\n\n"
        "CreditPay has detected suspicious activity "
        "associated with a payment attempt.\n\n"
        f"Amount: INR {amount:,.2f}\n"
        f"Card: {card_display}\n"
        f"Reference: {reference}\n"
        f"Payment Status: {payment_status}\n"
        f"Detection Details: {rule_details}\n"
    )

    if ip_address:
        message += f"Source IP: {ip_address}\n"

    message += (
        "\nIf you do not recognize this activity, "
        "please contact the support team immediately.\n\n"
        "Regards,\n"
        "CreditPay"
    )

    return _send_notification_email(
        recipient=recipient,
        subject=subject,
        message=message,
    )
