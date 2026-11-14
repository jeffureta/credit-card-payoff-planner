import pytest
from credit_planner.cli import main
from credit_planner.db import DatabaseManager
from credit_planner.models import CardProfile, StatementData
from datetime import date

def test_cli_help(capsys):
    with pytest.raises(SystemExit):
        main()

def test_cli_cards_empty(capsys, tmp_path, monkeypatch):
    db_path = str(tmp_path / "cli_test.db")
    monkeypatch.setattr("sys.argv", ["credit-planner", "--db", db_path, "cards"])
    main()
    captured = capsys.readouterr()
    assert "No credit cards found" in captured.out

def test_cli_plan_execution(capsys, tmp_path, monkeypatch):
    db_path = str(tmp_path / "cli_test.db")
    db = DatabaseManager(db_path)
    db.init_db()
    c_id = db.add_card(CardProfile(issuer="HSBC", card_name="HSBC Premier", last4="1234", current_apr=24.0))
    db.save_statement(StatementData(
        card_id=c_id,
        issuer="HSBC",
        statement_date=date(2026, 10, 1),
        statement_balance=1000.0,
        minimum_payment=50.0,
        due_date=date(2026, 10, 25),
        purchase_apr=24.0,
    ))

    monkeypatch.setattr("sys.argv", ["credit-planner", "--db", db_path, "plan", "--card-id", str(c_id), "--budget", "200"])
    main()
    captured = capsys.readouterr()
    assert "Payoff Schedule" in captured.out
    assert "Debt-free in" in captured.out

def test_cli_chat_single_shot(capsys, tmp_path, monkeypatch):
    db_path = str(tmp_path / "cli_test.db")
    db = DatabaseManager(db_path)
    db.init_db()
    c_id = db.add_card(CardProfile(issuer="HSBC", card_name="HSBC Premier", last4="1234", current_apr=24.0))
    db.save_statement(StatementData(
        card_id=c_id,
        issuer="HSBC",
        statement_date=date(2026, 10, 1),
        statement_balance=1000.0,
        minimum_payment=50.0,
        due_date=date(2026, 10, 25),
        purchase_apr=24.0,
    ))

    monkeypatch.setattr("sys.argv", ["credit-planner", "--db", db_path, "chat", "What should I pay?"])
    main()
    captured = capsys.readouterr()
    assert "AI Financial Advisor" in captured.out or "Debt Avalanche" in captured.out
