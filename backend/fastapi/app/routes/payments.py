
import uuid
from datetime import datetime, timedelta
from decimal import Decimal

from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    HTTPException,
    Request,
    status,
)
from sqlalchemy import func
from sqlalchemy.orm import Session

from ..auth import get_current_user
from ..db import get_db
from ..models import Card, FraudLog, Transaction, User
from ..notifications import (
    send_fraud_alert,
    send_high_value_transaction_alert,
    send_low_credit_alert,
)
from ..payment_service import simulate_payment
from ..schemas import PaymentRequest, PaymentResponse


router = APIRouter(
    prefix="/api/payments",
    tags=["Payments"],
)

HIGH_VALUE_THRESHOLD = Decimal("5000.00")
HIGH_VALUE_WINDOW = timedelta(minutes=10)
RAPID_ACTIVITY_WINDOW = timedelta(minutes=5)


def evaluate_fraud_rules(
    db: Session,
    transaction: Transaction,
    user_id: int,
):
    """
    Identify repeated high-value transactions and rapid activity
    with different location/device signals.
    """
    matched_rules = []
    transaction_time = transaction.created_at or datetime.utcnow()

    # Rule 1: Another high-value transaction in the previous 10 minutes.
    if transaction.amount > HIGH_VALUE_THRESHOLD:
        recent_high_value = (
            db.query(Transaction.id)
            .filter(
                Transaction.user_id == user_id,
                Transaction.id != transaction.id,
                Transaction.amount > HIGH_VALUE_THRESHOLD,
                Transaction.created_at
                >= transaction_time - HIGH_VALUE_WINDOW,
                Transaction.created_at <= transaction_time,
            )
            .first()
        )

        if recent_high_value:
            matched_rules.append(
                (
                    "MULTIPLE_HIGH_VALUE_TRANSACTIONS_10_MIN",
                    "Another transaction above INR 5,000 "
                    "occurred within the previous 10 minutes.",
                )
            )

    # Rule 2: Different location or device signals within five minutes.
    recent_transactions = (
        db.query(Transaction)
        .filter(
            Transaction.user_id == user_id,
            Transaction.id != transaction.id,
            Transaction.created_at
            >= transaction_time - RAPID_ACTIVITY_WINDOW,
            Transaction.created_at <= transaction_time,
        )
        .order_by(Transaction.created_at.desc())
        .limit(50)
        .all()
    )

    different_location = any(
        transaction.location
        and previous.location
        and transaction.location != previous.location
        for previous in recent_transactions
    )

    different_device = any(
        transaction.device_id
        and previous.device_id
        and transaction.device_id != previous.device_id
        for previous in recent_transactions
    )

    if different_location or different_device:
        changed_signals = []

        if different_location:
            changed_signals.append("location/IP signal changed")

        if different_device:
            changed_signals.append("device ID changed")

        matched_rules.append(
            (
                "RAPID_TRANSACTIONS_DIFFERENT_LOCATION_DEVICE",
                "Rapid transaction detected: "
                + " and ".join(changed_signals)
                + ".",
            )
        )

    return matched_rules


@router.post(
    "/",
    response_model=PaymentResponse,
    status_code=status.HTTP_201_CREATED,
)
def make_payment(
    payload: PaymentRequest,
    background_tasks: BackgroundTasks,
    request: Request,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    user_id = current_user["user_id"]

    # 1. Validate card ownership and active status.
    card = (
        db.query(Card)
        .filter(
            Card.id == payload.card_id,
            Card.user_id == user_id,
            Card.is_active.is_(True),
        )
        .first()
    )

    if card is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Card not found for this user.",
        )

    # 2. Validate the payment amount.
    if payload.amount <= Decimal("0"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Payment amount must be greater than zero.",
        )

    if payload.amount > Decimal("1000000"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Payment amount exceeds the allowed limit.",
        )

    # 3. Collect optional fraud-detection signals.
    client_ip = (
        request.client.host
        if request.client
        else ""
    )

    # Client location is an unverified signal, not GPS verification.
    location_signal = (
        request.headers.get(
            "x-client-location",
            "",
        ).strip()[:100]
        or client_ip[:100]
    )

    device_id = request.headers.get(
        "x-device-id",
        "",
    ).strip()[:128]

    # 4. Calculate successful card spending before this payment.
    spent_before = (
        db.query(
            func.coalesce(
                func.sum(Transaction.amount),
                0,
            )
        )
        .filter(
            Transaction.card_id == card.id,
            Transaction.user_id == user_id,
            Transaction.status == "SUCCESS",
        )
        .scalar()
        or Decimal("0.00")
    )

    spent_before = Decimal(str(spent_before))
    credit_limit = Decimal(str(card.credit_limit or 0))

    available_before = max(
        credit_limit - spent_before,
        Decimal("0.00"),
    )

    # 5. Create and persist the pending transaction.
    reference = f"PAY-{uuid.uuid4().hex[:16].upper()}"

    transaction = Transaction(
        user_id=user_id,
        card_id=card.id,
        amount=payload.amount,
        currency=payload.currency.upper(),
        status="PENDING",
        fraud_status="NOT_CHECKED",
        category=getattr(payload, "category", None) or "OTHER",
        location=location_signal,
        device_id=device_id,
        reference=reference,
        description=payload.description or "",
        failure_reason="",
    )

    db.add(transaction)
    db.commit()
    db.refresh(transaction)

    # 6. Evaluate fraud rules and save each matched rule.
    matched_rules = evaluate_fraud_rules(
        db=db,
        transaction=transaction,
        user_id=user_id,
    )

    if matched_rules:
        transaction.fraud_status = "FLAGGED"

        for rule_code, details in matched_rules:
            db.add(
                FraudLog(
                    user_id=user_id,
                    transaction_id=transaction.id,
                    rule_code=rule_code,
                    details=details,
                    ip_address=client_ip or None,
                    location=location_signal,
                    device_id=device_id,
                )
            )
    else:
        transaction.fraud_status = "CLEAR"

    db.commit()
    db.refresh(transaction)

    # 7. Preserve the existing payment simulation.
    # A fraud flag generates an alert; it does not automatically
    # reject a transaction in this rule-based implementation.
    payment_status, failure_reason = simulate_payment()

    transaction.status = payment_status
    transaction.failure_reason = failure_reason

    db.commit()
    db.refresh(transaction)

    # 8. Retrieve the user's email for notifications.
    user_email = (
        db.query(User.email)
        .filter(User.id == user_id)
        .scalar()
    )

    # 9. Fraud alert for a flagged payment attempt.
    if transaction.fraud_status == "FLAGGED" and user_email:
        background_tasks.add_task(
            send_fraud_alert,
            user_email,
            card.masked_number,
            transaction.amount,
            transaction.reference,
            transaction.status,
            "; ".join(details for _, details in matched_rules),
            client_ip,
        )

    # 10. High-value alert: preserve the existing > INR 5,000 rule.
    if (
        payment_status == "SUCCESS"
        and user_email
        and transaction.amount > HIGH_VALUE_THRESHOLD
    ):
        background_tasks.add_task(
            send_high_value_transaction_alert,
            user_email,
            transaction.amount,
            card.masked_number,
            transaction.reference,
        )

    # 11. Low-credit alert only when available credit crosses
    # from >= 10% to < 10% after a successful credit-card payment.
    if (
        payment_status == "SUCCESS"
        and user_email
        and card.card_type == "CREDIT"
        and credit_limit > Decimal("0.00")
    ):
        available_after = max(
            credit_limit - (spent_before + transaction.amount),
            Decimal("0.00"),
        )

        crossed_low_credit_threshold = (
            available_before / credit_limit >= Decimal("0.10")
            and available_after / credit_limit < Decimal("0.10")
        )

        if crossed_low_credit_threshold:
            background_tasks.add_task(
                send_low_credit_alert,
                user_email,
                available_after,
                credit_limit,
                card.masked_number,
            )

    # 12. Return the final payment result.
    return PaymentResponse(
        id=transaction.id,
        reference=transaction.reference,
        card_id=transaction.card_id,
        amount=transaction.amount,
        currency=transaction.currency,
        status=transaction.status,
        description=transaction.description,
        failure_reason=transaction.failure_reason,
        fraud_status=transaction.fraud_status,
        category=transaction.category,
    )
