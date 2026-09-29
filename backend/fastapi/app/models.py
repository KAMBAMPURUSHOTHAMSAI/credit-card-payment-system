from datetime import datetime

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
)

from sqlalchemy.orm import relationship

from .db import Base


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