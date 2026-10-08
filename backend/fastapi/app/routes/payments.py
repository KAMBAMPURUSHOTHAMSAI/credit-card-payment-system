import uuid
from decimal import Decimal

from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    HTTPException,
    status,
)

from sqlalchemy import func
from sqlalchemy.orm import Session

from ..auth import get_current_user
from ..db import get_db
from ..models import Card, Transaction, User
from ..notifications import (
    send_high_value_transaction_alert,
    send_low_credit_alert,
)
from ..payment_service import simulate_payment
from ..schemas import (
    PaymentRequest,
    PaymentResponse,
)


router = APIRouter(
    prefix="/api/payments",
    tags=["Payments"],
)


@router.post(
    "/",
    response_model=PaymentResponse,
    status_code=status.HTTP_201_CREATED,
)
def make_payment(
    payload: PaymentRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    user_id = current_user["user_id"]

    # =====================================================
    # 1. VALIDATE CARD OWNERSHIP
    # =====================================================

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

    # =====================================================
    # 2. VALIDATE PAYMENT AMOUNT
    # =====================================================

    if payload.amount <= Decimal("0"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "Payment amount must be "
                "greater than zero."
            ),
        )

    if payload.amount > Decimal("1000000"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "Payment amount exceeds "
                "the allowed limit."
            ),
        )

    # =====================================================
    # 3. CREATE PENDING TRANSACTION
    # =====================================================

    reference = (
        f"PAY-{uuid.uuid4().hex[:16].upper()}"
    )

    transaction = Transaction(
        user_id=user_id,
        card_id=card.id,
        amount=payload.amount,
        currency=payload.currency.upper(),
        status="PENDING",
        reference=reference,
        description=payload.description or "",
        failure_reason="",
    )

    db.add(transaction)
    db.commit()
    db.refresh(transaction)

    # =====================================================
    # 4. SIMULATE PAYMENT
    # =====================================================

    payment_status, failure_reason = (
        simulate_payment()
    )

    transaction.status = payment_status
    transaction.failure_reason = failure_reason

    db.commit()
    db.refresh(transaction)

    # =====================================================
    # 5. EMAIL NOTIFICATIONS
    #
    # Emails are scheduled only after the transaction
    # has been successfully committed.
    # =====================================================

    if payment_status == "SUCCESS":

        # -------------------------------------------------
        # GET USER EMAIL
        # -------------------------------------------------

        user_email = (
            db.query(User.email)
            .filter(
                User.id == user_id
            )
            .scalar()
        )

        # -------------------------------------------------
        # CALCULATE SUCCESSFUL SPENDING
        # -------------------------------------------------

        successful_spent = (
            db.query(
                func.coalesce(
                    func.sum(
                        Transaction.amount
                    ),
                    0,
                )
            )
            .filter(
                Transaction.card_id == card.id,
                Transaction.status == "SUCCESS",
            )
            .scalar()
        )

        if successful_spent is None:
            successful_spent = Decimal(
                "0.00"
            )

        successful_spent = Decimal(
            str(successful_spent)
        )

        # -------------------------------------------------
        # HIGH VALUE TRANSACTION ALERT
        # -------------------------------------------------

        if (
            user_email
            and transaction.amount > Decimal("5000.00")
        ):
            background_tasks.add_task(
                send_high_value_transaction_alert,
                user_email,
                transaction.amount,
                card.masked_number,
                transaction.reference,
            )

        # -------------------------------------------------
        # LOW CREDIT ALERT
        #
        # Trigger only when available credit crosses
        # from >= 10% to < 10%.
        # -------------------------------------------------

        if (
            user_email
            and card.card_type == "CREDIT"
            and card.credit_limit > Decimal("0.00")
        ):

            available_credit = (
                card.credit_limit
                - successful_spent
            )

            if available_credit < Decimal("0.00"):
                available_credit = Decimal(
                    "0.00"
                )

            # Spending before the current transaction.
            previous_successful_spent = (
                successful_spent
                - transaction.amount
            )

            if previous_successful_spent < Decimal(
                "0.00"
            ):
                previous_successful_spent = Decimal(
                    "0.00"
                )

            previous_available_credit = (
                card.credit_limit
                - previous_successful_spent
            )

            if previous_available_credit < Decimal(
                "0.00"
            ):
                previous_available_credit = Decimal(
                    "0.00"
                )

            previous_available_percentage = (
                previous_available_credit
                / card.credit_limit
            )

            current_available_percentage = (
                available_credit
                / card.credit_limit
            )

            crossed_low_credit_threshold = (
                previous_available_percentage
                >= Decimal("0.10")
                and current_available_percentage
                < Decimal("0.10")
            )

            if crossed_low_credit_threshold:

                background_tasks.add_task(
                    send_low_credit_alert,
                    user_email,
                    available_credit,
                    card.credit_limit,
                    card.masked_number,
                )

    # =====================================================
    # 6. RETURN FINAL RESULT
    # =====================================================

    return PaymentResponse(
        id=transaction.id,
        reference=transaction.reference,
        card_id=transaction.card_id,
        amount=transaction.amount,
        currency=transaction.currency,
        status=transaction.status,
        description=transaction.description,
        failure_reason=transaction.failure_reason,
    )