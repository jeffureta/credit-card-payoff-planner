import pytest
from datetime import date
from credit_planner.db import DatabaseManager
from credit_planner.models import CardProfile, StatementData, PaymentTarget
from credit_planner.ai.context_builder import build_financial_context_snapshot
from credit_planner.ai.assistant import AIAssistant

@pytest.fixture
def populated_db(tmp_path):
    db_file = str(tmp_path / "test_ai_planner.db")
    mgr = DatabaseManager(db_file)
    mgr.init_db()

    # Add 2 sample cards
    c1 = mgr.add_card(CardProfile(issuer="HSBC", card_name="HSBC Premier", last4="4321", current_apr=24.99))
    c2 = mgr.add_card(CardProfile(issuer="Chase", card_name="Chase Sapphire", last4="9012", current_apr=18.24))

    # Add statements
    mgr.save_statement(StatementData(
        card_id=c1,
        issuer="HSBC",
        statement_date=date(2026, 10, 1),
        statement_balance=4500.0,
        minimum_payment=120.0,
        due_date=date(2026, 10, 25),
        purchase_apr=24.99,
    ))
    mgr.save_statement(StatementData(
        card_id=c2,
        issuer="Chase",
        statement_date=date(2026, 10, 5),
        statement_balance=2500.0,
        minimum_payment=75.0,
        due_date=date(2026, 10, 30),
        purchase_apr=18.24,
    ))

    # Add portfolio target
    mgr.set_target(PaymentTarget(card_id=None, monthly_budget=500.0, strategy="AVALANCHE"))
    return mgr

def test_context_builder_snapshot(populated_db):
    snapshot = build_financial_context_snapshot(populated_db)
    
    assert "HSBC Premier" in snapshot
    assert "$4,500.00" in snapshot
    assert "Chase Sapphire" in snapshot
    assert "$2,500.00" in snapshot
    assert "24.99%" in snapshot
    assert "**Monthly Payment Budget**: $500.00" in snapshot
    assert "Avalanche" in snapshot

def test_ai_assistant_deterministic_fallback(populated_db):
    # Assistant should cleanly produce grounded advice even if Ollama/Gemini are offline
    assistant = AIAssistant(db=populated_db, mock_offline=True)
    response = assistant.ask("Which card should I pay off first?")

    assert "HSBC Premier" in response
    assert "24.99%" in response
