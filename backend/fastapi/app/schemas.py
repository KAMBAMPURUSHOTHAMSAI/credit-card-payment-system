from datetime import datetime
from decimal import Decimal
from typing import List, Optional

from pydantic import BaseModel, Field


class PaymentRequest(BaseModel):

    card_id: int = Field(
        gt=0
    )

    amount: Decimal = Field(
        gt=0,
        max_digits=12,
        decimal_places=2,
    )

    currency: str = Field(
        default="INR",
        min_length=3,
        max_length=3,
    )

    description: Optional[str] = Field(
        default=None,
        max_length=255,
    )


class PaymentResponse(BaseModel):

    id: int
    reference: str
    card_id: int
    amount: Decimal
    currency: str
    status: str
    description: str
    failure_reason: str


class DashboardTransaction(BaseModel):

    amount: Decimal
    masked_card_number: str
    date: datetime
    status: str


class DashboardSummary(BaseModel):

    total_transactions: int
    total_amount_spent: Decimal
    current_month_spending: Decimal
    available_credit_limit: Decimal
    last_5_transactions: List[DashboardTransaction]