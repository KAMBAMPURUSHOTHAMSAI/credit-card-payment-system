from datetime import datetime
from decimal import Decimal

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from sqlalchemy import func
from sqlalchemy.orm import Session

from .auth import get_current_user
from .db import get_db
from .models import Card, Transaction
from .routes.payments import router as payment_router


app = FastAPI(
    title="Credit Card Payment System - Payment API",
    description=(
        "Payment processing service "
        "for the Credit Card Payment System."
    ),
    version="1.0.0",
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(payment_router)


@app.get(
    "/dashboard/summary",
    tags=["Dashboard"],
)
def dashboard_summary(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """
    Return quick credit-card usage statistics
    for the currently authenticated user.
    """

    # -------------------------------------------------
    # CURRENT USER
    # -------------------------------------------------

    if isinstance(current_user, dict):
        user_id = current_user.get("user_id")
    elif hasattr(current_user, "user_id"):
        user_id = current_user.user_id
    else:
        user_id = current_user

    # -------------------------------------------------
    # CURRENT MONTH RANGE
    # -------------------------------------------------

    now = datetime.utcnow()

    month_start = now.replace(
        day=1,
        hour=0,
        minute=0,
        second=0,
        microsecond=0,
    )

    if now.month == 12:
        next_month_start = month_start.replace(
            year=now.year + 1,
            month=1,
        )
    else:
        next_month_start = month_start.replace(
            month=now.month + 1,
        )

    # -------------------------------------------------
    # TOTAL TRANSACTIONS
    # -------------------------------------------------

    total_transactions = (
        db.query(
            func.count(Transaction.id)
        )
        .filter(
            Transaction.user_id == user_id
        )
        .scalar()
        or 0
    )

    # -------------------------------------------------
    # TOTAL AMOUNT SPENT
    # -------------------------------------------------

    total_amount_spent = (
        db.query(
            func.coalesce(
                func.sum(Transaction.amount),
                0,
            )
        )
        .filter(
            Transaction.user_id == user_id
        )
        .scalar()
        or Decimal("0.00")
    )

    # -------------------------------------------------
    # CURRENT MONTH SPENDING
    # -------------------------------------------------

    current_month_spending = (
        db.query(
            func.coalesce(
                func.sum(Transaction.amount),
                0,
            )
        )
        .filter(
            Transaction.user_id == user_id,
            Transaction.created_at >= month_start,
            Transaction.created_at < next_month_start,
        )
        .scalar()
        or Decimal("0.00")
    )

    # -------------------------------------------------
    # TOTAL AVAILABLE CREDIT
    # -------------------------------------------------

    total_credit_limit = (
        db.query(
            func.coalesce(
                func.sum(Card.credit_limit),
                0,
            )
        )
        .filter(
            Card.user_id == user_id,
            Card.card_type == "CREDIT",
            Card.is_active.is_(True),
        )
        .scalar()
        or Decimal("0.00")
    )

    # -------------------------------------------------
    # SUCCESSFUL CREDIT CARD SPENDING
    # -------------------------------------------------

    credit_spent = (
        db.query(
            func.coalesce(
                func.sum(Transaction.amount),
                0,
            )
        )
        .join(
            Card,
            Transaction.card_id == Card.id,
        )
        .filter(
            Transaction.user_id == user_id,
            Card.user_id == user_id,
            Card.card_type == "CREDIT",
            Card.is_active.is_(True),
            Transaction.status == "SUCCESS",
        )
        .scalar()
        or Decimal("0.00")
    )

    # -------------------------------------------------
    # AVAILABLE CREDIT
    # -------------------------------------------------

    available_credit_limit = (
        total_credit_limit - credit_spent
    )

    if available_credit_limit < Decimal("0.00"):
        available_credit_limit = Decimal("0.00")

    # -------------------------------------------------
    # LAST 5 TRANSACTIONS
    # -------------------------------------------------

    recent_transactions = (
        db.query(
            Transaction.amount,
            Card.masked_number,
            Transaction.created_at,
            Transaction.status,
        )
        .join(
            Card,
            Transaction.card_id == Card.id,
        )
        .filter(
            Transaction.user_id == user_id,
            Card.user_id == user_id,
        )
        .order_by(
            Transaction.created_at.desc()
        )
        .limit(5)
        .all()
    )

    last_5_transactions = []

    for transaction in recent_transactions:
        last_5_transactions.append(
            {
                "amount": transaction.amount,
                "masked_card_number": (
                    transaction.masked_number
                ),
                "date": (
                    transaction.created_at.isoformat()
                ),
                "status": transaction.status,
            }
        )

    # -------------------------------------------------
    # RESPONSE
    # -------------------------------------------------

    return {
        "total_transactions": total_transactions,
        "total_amount_spent": total_amount_spent,
        "current_month_spending": current_month_spending,
        "available_credit_limit": available_credit_limit,
        "last_5_transactions": last_5_transactions,
    }


@app.get("/health", tags=["Health"])
def health_check():
    return {
        "status": "ok",
        "service": "fastapi-payment-service",
    }