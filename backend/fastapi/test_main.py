import jwt

import pytest

from fastapi.testclient import TestClient

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.auth import get_current_user
from app.config import settings
from app.db import Base, get_db
from app.main import app
from app.models import Card
from app.routes import payments as payments_route


# =========================================================
# TEST DATABASE
# =========================================================

TEST_DATABASE_URL = "sqlite://"

test_engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={
        "check_same_thread": False,
    },
    poolclass=StaticPool,
)


TestingSessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=test_engine,
)


# =========================================================
# DATABASE DEPENDENCY OVERRIDE
# =========================================================

def override_get_db():
    db = TestingSessionLocal()

    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[
    get_db
] = override_get_db


# =========================================================
# TEST CLIENT
# =========================================================

client = TestClient(app)


# =========================================================
# DATABASE FIXTURE
# =========================================================

@pytest.fixture
def db_session():

    Base.metadata.create_all(
        bind=test_engine
    )

    db = TestingSessionLocal()

    try:
        yield db

    finally:
        db.close()

        Base.metadata.drop_all(
            bind=test_engine
        )


# =========================================================
# AUTHENTICATED USER FIXTURE
# =========================================================

@pytest.fixture
def authenticated_user():

    app.dependency_overrides[
        get_current_user
    ] = lambda: {
        "user_id": 1,
        "payload": {
            "user_id": 1,
        },
    }

    yield

    app.dependency_overrides.pop(
        get_current_user,
        None,
    )


# =========================================================
# ACTIVE CARD FIXTURE
# =========================================================

@pytest.fixture
def active_card(db_session):

    card = Card(
        id=3,
        user_id=1,
        card_type="CREDIT",
        card_brand="VISA",
        masked_number="************1111",
        last4="1111",
        expiry_month=12,
        expiry_year=2030,
        is_active=True,
    )

    db_session.add(card)

    db_session.commit()

    db_session.refresh(card)

    return card


# =========================================================
# TEST 1 — HEALTH
# =========================================================

def test_health_check():

    response = client.get(
        "/health"
    )

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "ok"

    assert (
        data["service"]
        == "fastapi-payment-service"
    )


# =========================================================
# TEST 2 — DATABASE CONNECTION
# =========================================================

def test_payment_success(
    db_session,
    active_card,
    authenticated_user,
    monkeypatch,
):

    monkeypatch.setattr(
        payments_route,
        "simulate_payment",
        lambda: (
            "SUCCESS",
            "",
        ),
    )

    response = client.post(
        "/api/payments/",
        json={
            "card_id": active_card.id,
            "amount": 500.00,
            "currency": "INR",
            "description": "Test payment",
        },
    )

    assert (
        response.status_code
        == 201
    )

    data = response.json()

    assert data["status"] == "SUCCESS"

    assert (
        data["card_id"]
        == active_card.id
    )

    assert (
        data["amount"]
        == "500.00"
    )

    assert (
        data["failure_reason"]
        == ""
    )


# =========================================================
# TEST 6 — PAYMENT FAILURE
# =========================================================

def test_payment_failure(
    db_session,
    active_card,
    authenticated_user,
    monkeypatch,
):

    monkeypatch.setattr(
        payments_route,
        "simulate_payment",
        lambda: (
            "FAILED",
            "Simulated payment failure.",
        ),
    )

    response = client.post(
        "/api/payments/",
        json={
            "card_id": active_card.id,
            "amount": 500.00,
            "currency": "INR",
            "description": "Failed payment test",
        },
    )

    assert (
        response.status_code
        == 201
    )

    data = response.json()

    assert data["status"] == "FAILED"

    assert (
        data["failure_reason"]
        == "Simulated payment failure."
    )


# =========================================================
# TEST 7 — INVALID CARD
# =========================================================

def test_payment_invalid_card(
    db_session,
    authenticated_user,
):

    response = client.post(
        "/api/payments/",
        json={
            "card_id": 999,
            "amount": 500.00,
            "currency": "INR",
            "description": "Invalid card test",
        },
    )

    assert (
        response.status_code
        == 404
    )

    assert (
        response.json()["detail"]
        == "Card not found for this user."
    )


# =========================================================
# TEST 8 — CARD OWNERSHIP SECURITY
# =========================================================

def test_payment_card_belongs_to_user(
    db_session,
    authenticated_user,
):

    other_user_card = Card(
        id=99,
        user_id=999,
        card_type="CREDIT",
        card_brand="VISA",
        masked_number="************9999",
        last4="9999",
        expiry_month=12,
        expiry_year=2030,
        is_active=True,
    )

    db_session.add(
        other_user_card
    )

    db_session.commit()

    response = client.post(
        "/api/payments/",
        json={
            "card_id": 99,
            "amount": 500.00,
            "currency": "INR",
            "description": (
                "Ownership security test"
            ),
        },
    )

    assert (
        response.status_code
        == 404
    )


# =========================================================
# TEST 9 — ZERO AMOUNT
# =========================================================

def test_payment_zero_amount(
    active_card,
    authenticated_user,
):

    response = client.post(
        "/api/payments/",
        json={
            "card_id": active_card.id,
            "amount": 0,
            "currency": "INR",
            "description": "Zero amount",
        },
    )

    assert (
        response.status_code
        == 422
    )
