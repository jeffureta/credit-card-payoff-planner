"""Domain models for Universal Credit Card Statement Parser & Payoff Planner."""
from dataclasses import dataclass, field
from datetime import date
from enum import Enum
from typing import Optional


class VarianceStatus(str, Enum):
    AHEAD = "AHEAD"
    ON_TARGET = "ON_TARGET"
    BEHIND = "BEHIND"


@dataclass
class CardProfile:
    id: Optional[int] = None
    issuer: str = ""
    card_name: str = ""
    last4: str = ""
    current_apr: float = 0.0
    credit_limit: float = 0.0


@dataclass
class StatementData:
    statement_date: date
    statement_balance: float
    minimum_payment: float
    due_date: date
    purchase_apr: float
    issuer: str = ""
    card_id: Optional[int] = None
    account_last4: str = ""
    currency: str = "USD"
    raw_file_hash: Optional[str] = None


@dataclass
class PaymentTarget:
    card_id: Optional[int] = None  # None indicates portfolio-level target
    target_date: Optional[date] = None
    monthly_budget: float = 0.0
    strategy: str = "AVALANCHE"  # AVALANCHE or SNOWBALL


@dataclass
class PaymentRecord:
    card_id: int
    payment_date: date
    amount: float
    id: Optional[int] = None


@dataclass
class ProgressReport:
    card_id: int
    card_name: str
    actual_balance: float
    expected_balance: float
    variance: float  # Positive = paid down more than expected (ahead)
    status: VarianceStatus
