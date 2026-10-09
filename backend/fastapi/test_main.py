import asyncio
import logging
from datetime import datetime, timedelta
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from starlette.requests import Request

from app.auth import get_current_user
from app.db import Base, get_db
from app.main import app, request_monitoring_middleware
from app.models import Card, FraudLog, Transaction, User
from app.routes import payments as payments_route


# =========================================================
# TEST DATABASE
# =========================================================

TEST_DATABASE_URL = "sqlite://"

test_engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
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


app.dependency_overrides[get_db] = override_get_db


# =========================================================
# TEST CLIENT
# =========================================================

client = TestClient(app)


# =========================================================
# DATABASE FIXTURE
# =========================================================

@pytest.fixture
def db_session():
    Base.metadata.create_all(bind=test_engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=test_engine)


# =========================================================
# AUTHENTICATED USER FIXTURE
# =========================================================

@pytest.fixture
def authenticated_user():
    app.dependency_overrides[get_current_user] = lambda: {
        "user_id": 1,
        "payload": {"user_id": 1},
    }
    yield
    app.dependency_overrides.pop(get_current_user, None)


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
        credit_limit=Decimal("10000.00"),
        is_active=True,
    )
    db_session.add(card)
    db_session.commit()
    db_session.refresh(card)
    return card


# =========================================================
# TEST 1 — HEALTH ENDPOINT
# =========================================================

def test_health_check():
    response = client.get("/health")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["service"] == "fastapi-payment-service"


# =========================================================
# TEST 2 — SUCCESSFUL PAYMENT
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
        lambda: ("SUCCESS", ""),
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

    assert response.status_code == 201
    data = response.json()
    assert data["status"] == "SUCCESS"
    assert data["card_id"] == active_card.id
    assert data["amount"] == "500.00"
    assert data["failure_reason"] == ""


# =========================================================
# TEST 3 — FAILED PAYMENT
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
        lambda: ("FAILED", "Simulated payment failure."),
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

    assert response.status_code == 201
    data = response.json()
    assert data["status"] == "FAILED"
    assert data["failure_reason"] == "Simulated payment failure."


# =========================================================
# TEST 4 — INVALID CARD
# =========================================================

def test_payment_invalid_card(db_session, authenticated_user):
    response = client.post(
        "/api/payments/",
        json={
            "card_id": 999,
            "amount": 500.00,
            "currency": "INR",
            "description": "Invalid card test",
        },
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Card not found for this user."


# =========================================================
# TEST 5 — CARD OWNERSHIP SECURITY
# =========================================================

def test_payment_card_belongs_to_user(db_session, authenticated_user):
    other_user_card = Card(
        id=99,
        user_id=999,
        card_type="CREDIT",
        card_brand="VISA",
        masked_number="************9999",
        last4="9999",
        expiry_month=12,
        expiry_year=2030,
        credit_limit=Decimal("10000.00"),
        is_active=True,
    )
    db_session.add(other_user_card)
    db_session.commit()

    response = client.post(
        "/api/payments/",
        json={
            "card_id": 99,
            "amount": 500.00,
            "currency": "INR",
            "description": "Ownership security test",
        },
    )

    assert response.status_code == 404


# =========================================================
# TEST 6 — ZERO AMOUNT VALIDATION
# =========================================================

def test_payment_zero_amount(active_card, authenticated_user):
    response = client.post(
        "/api/payments/",
        json={
            "card_id": active_card.id,
            "amount": 0,
            "currency": "INR",
            "description": "Zero amount",
        },
    )

    # The request schema may reject zero before the route runs.
    assert response.status_code == 422


# =========================================================
# TEST 7 — HIGH-VALUE TRANSACTION EMAIL
# =========================================================

def test_high_value_notification(
    db_session,
    active_card,
    authenticated_user,
    monkeypatch,
):
    db_session.add(User(id=1, email="alerts@example.com"))
    db_session.commit()

    monkeypatch.setattr(
        payments_route,
        "simulate_payment",
        lambda: ("SUCCESS", ""),
    )

    sent_notifications = []
    monkeypatch.setattr(
        payments_route,
        "send_high_value_transaction_alert",
        lambda *args: sent_notifications.append(args),
    )
    monkeypatch.setattr(
        payments_route,
        "send_low_credit_alert",
        lambda *args: None,
    )

    response = client.post(
        "/api/payments/",
        json={
            "card_id": active_card.id,
            "amount": 6000.00,
            "currency": "INR",
            "description": "High value test",
        },
    )

    assert response.status_code == 201
    assert sent_notifications
    assert sent_notifications[0][0] == "alerts@example.com"


# =========================================================
# TEST 8 — LOW-CREDIT EMAIL
# =========================================================

def test_low_credit_notification(
    db_session,
    active_card,
    authenticated_user,
    monkeypatch,
):
    db_session.add(User(id=1, email="alerts@example.com"))
    db_session.commit()

    monkeypatch.setattr(
        payments_route,
        "simulate_payment",
        lambda: ("SUCCESS", ""),
    )

    low_credit_notifications = []
    monkeypatch.setattr(
        payments_route,
        "send_low_credit_alert",
        lambda *args: low_credit_notifications.append(args),
    )
    monkeypatch.setattr(
        payments_route,
        "send_high_value_transaction_alert",
        lambda *args: None,
    )

    response = client.post(
        "/api/payments/",
        json={
            "card_id": active_card.id,
            "amount": 9200.00,
            "currency": "INR",
            "description": "Low credit test",
        },
    )

    assert response.status_code == 201
    assert low_credit_notifications
    assert low_credit_notifications[0][0] == "alerts@example.com"


# =========================================================
# TEST 9 — FRAUD DETECTION, LOGGING AND ALERT
# =========================================================

def test_fraud_detection_logs_and_sends_alert(
    db_session,
    active_card,
    authenticated_user,
    monkeypatch,
):
    db_session.add(User(id=1, email="fraud-alerts@example.com"))
    db_session.flush()

    previous_time = datetime.utcnow() - timedelta(minutes=2)
    previous_transaction = Transaction(
        user_id=1,
        card_id=active_card.id,
        amount=Decimal("6000.00"),
        currency="INR",
        status="SUCCESS",
        fraud_status="CLEAR",
        category="SHOPPING",
        location="198.51.100.10",
        device_id="previous-device",
        reference="PAY-FRAUD-PREVIOUS",
        description="Previous transaction",
        failure_reason="",
        created_at=previous_time,
        updated_at=previous_time,
    )
    db_session.add(previous_transaction)
    db_session.commit()

    monkeypatch.setattr(
        payments_route,
        "simulate_payment",
        lambda: ("SUCCESS", ""),
    )

    fraud_notifications = []
    monkeypatch.setattr(
        payments_route,
        "send_fraud_alert",
        lambda *args: fraud_notifications.append(args),
    )
    monkeypatch.setattr(
        payments_route,
        "send_high_value_transaction_alert",
        lambda *args: None,
    )
    monkeypatch.setattr(
        payments_route,
        "send_low_credit_alert",
        lambda *args: None,
    )

    response = client.post(
        "/api/payments/",
        headers={
            "X-Forwarded-For": "203.0.113.20",
            "X-Client-Location": "New Location",
            "X-Device-ID": "new-device",
        },
        json={
            "card_id": active_card.id,
            "amount": 6500.00,
            "currency": "INR",
            "category": "FOOD",
            "description": "Fraud detection test",
        },
    )

    assert response.status_code == 201
    data = response.json()
    assert data["fraud_status"] == "FLAGGED"
    assert data["category"] == "FOOD"
    assert db_session.query(FraudLog).count() >= 1
    assert fraud_notifications


# =========================================================
# TEST 10 — REQUEST-TIME LOGGING
# =========================================================

def test_request_monitoring_logs_response_time(caplog):
    caplog.set_level(logging.INFO, logger="api.monitoring")

    response = client.get("/health")

    assert response.status_code == 200
    assert any(
        record.name == "api.monitoring"
        and "FastAPI request:" in record.getMessage()
        and "path=/health" in record.getMessage()
        and "status=200" in record.getMessage()
        and "duration_ms=" in record.getMessage()
        for record in caplog.records
    )


# =========================================================
# TEST 11 — CLIENT ERROR LOGGING
# =========================================================

def test_request_monitoring_logs_4xx_as_warning(caplog):
    caplog.set_level(logging.WARNING, logger="api.monitoring")

    response = client.get("/__route_that_does_not_exist_for_test__")

    assert response.status_code == 404
    assert any(
        record.name == "api.monitoring"
        and record.levelno == logging.WARNING
        and "status=404" in record.getMessage()
        for record in caplog.records
    )


# =========================================================
# TEST 12 — UNHANDLED EXCEPTION LOGGING
# =========================================================

def test_request_monitoring_logs_unhandled_exception(caplog):
    caplog.set_level(logging.ERROR, logger="api.monitoring")
    request = Request(
        {
            "type": "http",
            "asgi": {"version": "3.0"},
            "http_version": "1.1",
            "method": "GET",
            "scheme": "http",
            "path": "/__test_exception__",
            "raw_path": b"/__test_exception__",
            "query_string": b"",
            "headers": [],
            "server": ("testserver", 80),
            "client": ("testclient", 12345),
        }
    )

    async def raise_test_exception(_request):
        raise RuntimeError("test-only exception")

    with pytest.raises(RuntimeError, match="test-only exception"):
        asyncio.run(
            request_monitoring_middleware(
                request,
                raise_test_exception,
            )
        )

    assert any(
        record.name == "api.monitoring"
        and "FastAPI request exception" in record.getMessage()
        and "path=/__test_exception__" in record.getMessage()
        for record in caplog.records
    )
