import random
import uuid
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..auth import get_current_user
from ..config import settings
from ..db import get_db
from ..models import Card, Transaction
from ..schemas import PaymentRequest, PaymentResponse


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
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    user_id = current_user["user_id"]

    # -----------------------------------------------------
    # 1. Validate card
    # -----------------------------------------------------

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

    # -----------------------------------------------------
    # 2. Validate amount
    # -----------------------------------------------------

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

    # -----------------------------------------------------
    # 3. Create transaction as PENDING
    # -----------------------------------------------------

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

    # -----------------------------------------------------
    # 4. Simulate payment
    # -----------------------------------------------------

    random_value = random.randint(1, 100)

    if random_value <= settings.PAYMENT_SUCCESS_RATE:
        transaction.status = "SUCCESS"
        transaction.failure_reason = ""

    else:
        transaction.status = "FAILED"
        transaction.failure_reason = (
            "Simulated payment failure."
        )

    db.commit()
    db.refresh(transaction)

    # -----------------------------------------------------
    # 5. Return final result
    # -----------------------------------------------------

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