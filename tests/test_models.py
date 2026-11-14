import pytest
from datetime import date
from credit_planner.models import (
    CardProfile,
    StatementData,
    PaymentTarget,
    PaymentRecord,
    ProgressReport,
    VarianceStatus,
)

def test_card_profile_initialization():
    card = CardProfile(
        id=1,
        issuer="HSBC",
        card_name="HSBC Premier World",
        last4="4321",
        current_apr=24.99,
        credit_limit=10000.0,
    )
    assert card.id == 1
    assert card.issuer == "HSBC"
    assert card.current_apr == 24.99

def test_statement_data_validation():
    stmt = StatementData(
        card_id=1,
        issuer="HSBC",
        statement_date=date(2026, 10, 15),
        statement_balance=4500.50,
        minimum_payment=120.00,
        due_date=date(2026, 11, 10),
        purchase_apr=24.99,
        currency="USD",
    )
    assert stmt.statement_balance == 4500.50
    assert stmt.currency == "USD"

def test_progress_report_variance_status():
    report = ProgressReport(
        card_id=1,
        card_name="HSBC Premier",
        actual_balance=3800.0,
        expected_balance=4000.0,
        variance=200.0,  # paid $200 more than target expected
        status=VarianceStatus.AHEAD,
    )
    assert report.status == VarianceStatus.AHEAD
    assert report.variance == 200.0
