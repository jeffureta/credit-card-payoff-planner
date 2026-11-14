import os
import pytest
from datetime import date
from unittest.mock import patch
from credit_planner.db import DatabaseManager
from credit_planner.cli import main, verify_statement_integrity
from credit_planner.models import StatementData


def test_verify_statement_integrity_success():
    stmt = StatementData(
        statement_date=date(2026, 11, 7),
        statement_balance=2234.63,
        minimum_payment=121.91,
        due_date=date(2026, 12, 3),
        purchase_apr=30.34,
        account_last4="6067",
        issuer="Capital One",
    )
    is_valid, reasons = verify_statement_integrity(stmt)
    assert is_valid is True
    assert len(reasons) == 0


def test_verify_statement_integrity_failures():
    # Balance 0, min payment 0, last4 '0000', invalid issuer
    stmt = StatementData(
        statement_date=date.today(),
        statement_balance=0.0,
        minimum_payment=0.0,
        due_date=date.today(),
        purchase_apr=0.0,
        account_last4="0000",
        issuer="Generic",
    )
    is_valid, reasons = verify_statement_integrity(stmt)
    assert is_valid is False
    assert any("balance" in r.lower() for r in reasons)
    assert any("minimum payment" in r.lower() for r in reasons)
    assert any("last 4" in r.lower() for r in reasons)


def test_batch_parse_directory_and_safe_delete(tmp_path):
    # Setup temp DB
    db_path = str(tmp_path / "test.db")
    stmt_dir = tmp_path / "statements"
    stmt_dir.mkdir()

    # Create dummy files: one valid mock PDF and one invalid mock PDF
    pdf_path = stmt_dir / "statement1.pdf"
    pdf_path.write_text("Dummy content")

    valid_stmt = StatementData(
        statement_date=date(2026, 11, 7),
        statement_balance=1000.0,
        minimum_payment=50.0,
        due_date=date(2026, 12, 1),
        purchase_apr=20.0,
        account_last4="1234",
        issuer="Capital One",
    )

    # Mock extract_text_from_pdf and parser to return valid_stmt
    with patch("credit_planner.cli.extract_text_from_pdf", return_value="dummy text"):
        with patch("credit_planner.cli.ParserRegistry") as mock_reg_cls:
            mock_reg = mock_reg_cls.return_value
            mock_parser = mock_reg.resolve_for_text.return_value
            mock_parser.parse_text.return_value = valid_stmt

            # 1. Parse without delete flag -> file remains
            with patch("sys.argv", ["credit-planner", "--db", db_path, "parse", str(stmt_dir)]):
                main()
            assert pdf_path.exists()

            # 2. Parse with delete flag -> file is safely deleted because it passed 100% verification
            with patch("sys.argv", ["credit-planner", "--db", db_path, "parse", str(stmt_dir), "--delete-after-parse", "--yes"]):
                main()
            assert not pdf_path.exists()
