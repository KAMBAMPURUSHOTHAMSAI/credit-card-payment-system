
from datetime import datetime

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
)

from sqlalchemy.orm import relationship

from .db import Base


class User(Base):
    """
    Read-only mapping of the existing Django user table.

    FastAPI uses this mapping to retrieve the authenticated
    user's email for notifications.
    """

    __tablename__ = "accounts_user"

    id = Column(
        Integer,
        primary_key=True,
    )

    email = Column(
        String(254),
        nullable=False,
    )


class Card(Base):
    __tablename__ = "payments_card"

    id = Column(
        Integer,
        primary_key=True,
    )

    user_id = Column(
        Integer,
        nullable=False,
    )

    card_type = Column(
        String(10),
        nullable=False,
    )

    card_brand = Column(
        String(30),
        nullable=False,
    )

    masked_number = Column(
        String(20),
        nullable=False,
    )

    last4 = Column(
        String(4),
        nullable=False,
    )

    expiry_month = Column(
        Integer,
        nullable=False,
    )

    expiry_year = Column(
        Integer,
        nullable=False,
    )

    credit_limit = Column(
        Numeric(12, 2),
        nullable=False,
        default=0,
    )

    is_active = Column(
        Boolean,
        nullable=False,
    )


class Transaction(Base):
    __tablename__ = "payments_transaction"

    id = Column(
        Integer,
        primary_key=True,
    )

    user_id = Column(
        Integer,
        nullable=False,
    )

    card_id = Column(
        Integer,
        ForeignKey("payments_card.id"),
        nullable=False,
    )

    amount = Column(
        Numeric(12, 2),
        nullable=False,
    )

    currency = Column(
        String(3),
        nullable=False,
    )

    status = Column(
        String(10),
        nullable=False,
    )

    # Fraud detection result
    fraud_status = Column(
        String(15),
        nullable=False,
        default="NOT_CHECKED",
        index=True,
    )

    # Category-wise spending analytics
    category = Column(
        String(50),
        nullable=False,
        default="OTHER",
        index=True,
    )

    # Optional fraud detection signals
    location = Column(
        String(100),
        nullable=False,
        default="",
    )

    device_id = Column(
        String(128),
        nullable=False,
        default="",
    )

    reference = Column(
        String(64),
        nullable=False,
        unique=True,
    )

    description = Column(
        String(255),
        nullable=False,
        default="",
    )

    failure_reason = Column(
        String(255),
        nullable=False,
        default="",
    )

    created_at = Column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        index=True,
    )

    updated_at = Column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )

    card = relationship(
        "Card",
        lazy="joined",
    )


class FraudLog(Base):
    """
    Stores suspicious transaction events and the rule
    that triggered each fraud alert.
    """

    __tablename__ = "payments_fraudlog"

    id = Column(
        Integer,
        primary_key=True,
    )

    user_id = Column(
        Integer,
        ForeignKey(
            "accounts_user.id",
            ondelete="SET NULL",
        ),
        nullable=True,
    )

    transaction_id = Column(
        Integer,
        ForeignKey(
            "payments_transaction.id",
            ondelete="SET NULL",
        ),
        nullable=True,
    )

    rule_code = Column(
        String(100),
        nullable=False,
    )

    details = Column(
        Text,
        nullable=False,
        default="",
    )

    ip_address = Column(
        String(39),
        nullable=True,
    )

    location = Column(
        String(100),
        nullable=False,
        default="",
    )

    device_id = Column(
        String(128),
        nullable=False,
        default="",
    )

    created_at = Column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        index=True,
    )

    user = relationship(
        "User",
        lazy="joined",
    )

    transaction = relationship(
        "Transaction",
        lazy="joined",
    )
