import pytest
import sqlite3
from datetime import date
from credit_planner.db import DatabaseManager
from credit_planner.models import CardProfile, StatementData, PaymentTarget, PaymentRecord, VarianceStatus

@pytest.fixture
def db(tmp_path):
    db_file = str(tmp_path / "test_planner.db")
    manager = DatabaseManager(db_file)
    manager.init_db()
    return manager

def test_add_and_get_card(db):
    card = CardProfile(
        issuer="HSBC",
        card_name="HSBC Premier World",
        last4="9876",
        current_apr=22.49,
        credit_limit=15000.0,
    )
    card_id = db.add_card(card)
    assert card_id is not None
    assert card_id > 0

    cards = db.get_cards()
    assert len(cards) == 1
    assert cards[0].id == card_id
    assert cards[0].issuer == "HSBC"
    assert cards[0].last4 == "9876"

def test_save_and_retrieve_statements(db):
    card_id = db.add_card(CardProfile(issuer="Chase", card_name="Sapphire Reserve", last4="1111", current_apr=28.24))
    
    stmt1 = StatementData(
        card_id=card_id,
        issuer="Chase",
        statement_date=date(2026, 9, 1),
        statement_balance=3200.00,
        minimum_payment=100.00,
        due_date=date(2026, 9, 25),
        purchase_apr=28.24,
    )
    stmt2 = StatementData(
        card_id=card_id,
        issuer="Chase",
        statement_date=date(2026, 10, 1),
        statement_balance=2900.00,
        minimum_payment=95.00,
        due_date=date(2026, 10, 25),
        purchase_apr=28.24,
    )
    db.save_statement(stmt1)
    db.save_statement(stmt2)

    history = db.get_statements_for_card(card_id)
    assert len(history) == 2
    # Verify latest statement is first
    assert history[0].statement_date == date(2026, 10, 1)
    assert history[0].statement_balance == 2900.00

def test_progress_tracking_variance(db):
    card_id = db.add_card(CardProfile(issuer="Citi", card_name="Double Cash", last4="2222", current_apr=20.0))
    # Starting statement
    db.save_statement(StatementData(
        card_id=card_id,
        issuer="Citi",
        statement_date=date(2026, 8, 1),
        statement_balance=5000.00,
        minimum_payment=150.00,
        due_date=date(2026, 8, 25),
        purchase_apr=20.0,
    ))
    # Target: pay $500/month
    db.set_target(PaymentTarget(card_id=card_id, monthly_budget=500.0))
    
    # Next statement reflects aggressive paydown to $4300 (expected ~4583 after interest)
    db.save_statement(StatementData(
        card_id=card_id,
        issuer="Citi",
        statement_date=date(2026, 9, 1),
        statement_balance=4300.00,
        minimum_payment=140.00,
        due_date=date(2026, 9, 25),
        purchase_apr=20.0,
    ))
    
    report = db.get_progress_report(card_id)
    assert report is not None
    assert report.actual_balance == 4300.00
    assert report.status == VarianceStatus.AHEAD
