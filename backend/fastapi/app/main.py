from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from sqlalchemy.orm import Session

from .auth import get_current_user
from .db import get_db
from .models import Card
from .routes.payments import router as payment_router


app = FastAPI(
    title="Credit Card Payment System - Payment API",
    description=(
        "Payment processing service "
        "for the Credit Card Payment System."
    ),
    version="1.0.0",
)


# =========================================================
# CORS
# =========================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=[
        "*",
    ],
    allow_headers=[
        "*",
    ],
)


# =========================================================
# ROUTERS
# =========================================================

app.include_router(
    payment_router
)


# =========================================================
# HEALTH
# =========================================================

@app.get(
    "/health",
    tags=["Health"],
)
def health_check():
    return {
        "status": "ok",
        "service": "fastapi-payment-service",
    }


# =========================================================
# DATABASE CHECK
# =========================================================

@app.get(
    "/database-check",
    tags=["Health"],
)
def database_check(
    db: Session = Depends(get_db),
):
    result = db.execute(
        text("SELECT 1")
    )

    return {
        "database": "connected",
        "result": result.scalar(),
    }


# =========================================================
# DATABASE CARD TEST
# =========================================================

@app.get(
    "/database/cards",
    tags=["Database Test"],
)
def database_cards(
    db: Session = Depends(get_db),
):
    cards = (
        db.query(Card)
        .filter(
            Card.is_active.is_(True)
        )
        .all()
    )

    return {
        "count": len(cards),
        "cards": [
            {
                "id": card.id,
                "user_id": card.user_id,
                "card_type": card.card_type,
                "card_brand": card.card_brand,
                "masked_number": card.masked_number,
                "last4": card.last4,
                "expiry_month": card.expiry_month,
                "expiry_year": card.expiry_year,
            }
            for card in cards
        ],
    }


# =========================================================
# JWT TEST
# =========================================================

@app.get(
    "/auth-test",
    tags=["Authentication"],
)
def auth_test(
    current_user=Depends(
        get_current_user
    ),
):
    return {
        "authenticated": True,
        "user_id": current_user["user_id"],
    }