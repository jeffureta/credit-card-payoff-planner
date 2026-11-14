"""SQLite database manager for multi-card credit planner."""
import sqlite3
import os
from datetime import date
from typing import List, Optional
from credit_planner.models import (
    CardProfile,
    StatementData,
    PaymentTarget,
    PaymentRecord,
    ProgressReport,
    VarianceStatus,
)


class DatabaseManager:
    def __init__(self, db_path: str = "data/credit_planner.db"):
        self.db_path = db_path
        os.makedirs(os.path.dirname(os.path.abspath(db_path)), exist_ok=True)

    def get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def init_db(self) -> None:
        with self.get_connection() as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS cards (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    issuer TEXT NOT NULL,
                    card_name TEXT NOT NULL,
                    last4 TEXT NOT NULL,
                    current_apr REAL NOT NULL DEFAULT 0.0,
                    credit_limit REAL NOT NULL DEFAULT 0.0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(issuer, last4)
                );

                CREATE TABLE IF NOT EXISTS statements (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    card_id INTEGER NOT NULL,
                    statement_date TEXT NOT NULL,
                    statement_balance REAL NOT NULL,
                    minimum_payment REAL NOT NULL,
                    due_date TEXT NOT NULL,
                    purchase_apr REAL NOT NULL,
                    currency TEXT NOT NULL DEFAULT 'USD',
                    raw_file_hash TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (card_id) REFERENCES cards(id) ON DELETE CASCADE
                );

                CREATE TABLE IF NOT EXISTS payment_targets (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    card_id INTEGER UNIQUE,
                    target_date TEXT,
                    monthly_budget REAL NOT NULL DEFAULT 0.0,
                    strategy TEXT NOT NULL DEFAULT 'AVALANCHE',
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (card_id) REFERENCES cards(id) ON DELETE CASCADE
                );

                CREATE TABLE IF NOT EXISTS payment_records (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    card_id INTEGER NOT NULL,
                    payment_date TEXT NOT NULL,
                    amount REAL NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (card_id) REFERENCES cards(id) ON DELETE CASCADE
                );
            """)

    def add_card(self, card: CardProfile) -> int:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO cards (issuer, card_name, last4, current_apr, credit_limit)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(issuer, last4) DO UPDATE SET
                    card_name=excluded.card_name,
                    current_apr=excluded.current_apr,
                    credit_limit=excluded.credit_limit
            """, (card.issuer, card.card_name, card.last4, card.current_apr, card.credit_limit))
            if cursor.lastrowid:
                return cursor.lastrowid
            # Retrieve existing id if updated
            cursor.execute("SELECT id FROM cards WHERE issuer=? AND last4=?", (card.issuer, card.last4))
            row = cursor.fetchone()
            return row["id"]

    def get_cards(self) -> List[CardProfile]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, issuer, card_name, last4, current_apr, credit_limit FROM cards ORDER BY id ASC")
            rows = cursor.fetchall()
            return [
                CardProfile(
                    id=row["id"],
                    issuer=row["issuer"],
                    card_name=row["card_name"],
                    last4=row["last4"],
                    current_apr=row["current_apr"],
                    credit_limit=row["credit_limit"],
                )
                for row in rows
            ]

    def get_card(self, card_id: int) -> Optional[CardProfile]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, issuer, card_name, last4, current_apr, credit_limit FROM cards WHERE id=?", (card_id,))
            row = cursor.fetchone()
            if not row:
                return None
            return CardProfile(
                id=row["id"],
                issuer=row["issuer"],
                card_name=row["card_name"],
                last4=row["last4"],
                current_apr=row["current_apr"],
                credit_limit=row["credit_limit"],
            )

    def save_statement(self, stmt: StatementData) -> int:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO statements (card_id, statement_date, statement_balance, minimum_payment, due_date, purchase_apr, currency, raw_file_hash)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                stmt.card_id,
                stmt.statement_date.isoformat(),
                stmt.statement_balance,
                stmt.minimum_payment,
                stmt.due_date.isoformat(),
                stmt.purchase_apr,
                stmt.currency,
                stmt.raw_file_hash,
            ))
            # Also update card current APR
            if stmt.card_id and stmt.purchase_apr > 0:
                cursor.execute("UPDATE cards SET current_apr=? WHERE id=?", (stmt.purchase_apr, stmt.card_id))
            return cursor.lastrowid

    def get_statements_for_card(self, card_id: int) -> List[StatementData]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT s.*, c.issuer, c.last4
                FROM statements s
                JOIN cards c ON s.card_id = c.id
                WHERE s.card_id = ?
                ORDER BY s.statement_date DESC
            """, (card_id,))
            rows = cursor.fetchall()
            return [
                StatementData(
                    card_id=row["card_id"],
                    issuer=row["issuer"],
                    account_last4=row["last4"],
                    statement_date=date.fromisoformat(row["statement_date"]),
                    statement_balance=row["statement_balance"],
                    minimum_payment=row["minimum_payment"],
                    due_date=date.fromisoformat(row["due_date"]),
                    purchase_apr=row["purchase_apr"],
                    currency=row["currency"],
                    raw_file_hash=row["raw_file_hash"],
                )
                for row in rows
            ]

    def set_target(self, target: PaymentTarget) -> None:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO payment_targets (card_id, target_date, monthly_budget, strategy)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(card_id) DO UPDATE SET
                    target_date=excluded.target_date,
                    monthly_budget=excluded.monthly_budget,
                    strategy=excluded.strategy,
                    updated_at=CURRENT_TIMESTAMP
            """, (
                target.card_id,
                target.target_date.isoformat() if target.target_date else None,
                target.monthly_budget,
                target.strategy,
            ))

    def get_target(self, card_id: Optional[int]) -> Optional[PaymentTarget]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM payment_targets WHERE card_id IS ?", (card_id,))
            row = cursor.fetchone()
            if not row:
                return None
            return PaymentTarget(
                card_id=row["card_id"],
                target_date=date.fromisoformat(row["target_date"]) if row["target_date"] else None,
                monthly_budget=row["monthly_budget"],
                strategy=row["strategy"],
            )

    def log_payment(self, record: PaymentRecord) -> int:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO payment_records (card_id, payment_date, amount)
                VALUES (?, ?, ?)
            """, (record.card_id, record.payment_date.isoformat(), record.amount))
            return cursor.lastrowid

    def get_progress_report(self, card_id: int) -> Optional[ProgressReport]:
        card = self.get_card(card_id)
        if not card:
            return None
        
        statements = self.get_statements_for_card(card_id)
        if len(statements) < 1:
            return None
        
        latest_stmt = statements[0]
        actual_balance = latest_stmt.statement_balance
        target = self.get_target(card_id)

        if len(statements) >= 2 and target and target.monthly_budget > 0:
            previous_stmt = statements[1]
            prev_balance = previous_stmt.statement_balance
            monthly_rate = (previous_stmt.purchase_apr / 100.0) / 12.0
            accrued_interest = prev_balance * monthly_rate
            expected_balance = max(0.0, prev_balance + accrued_interest - target.monthly_budget)
        else:
            # Baseline expected is either latest or previous
            expected_balance = actual_balance

        variance = expected_balance - actual_balance  # positive = balance is lower than expected
        
        # Determine status
        tolerance = 10.0  # $10 tolerance window
        if variance > tolerance:
            status = VarianceStatus.AHEAD
        elif variance < -tolerance:
            status = VarianceStatus.BEHIND
        else:
            status = VarianceStatus.ON_TARGET

        return ProgressReport(
            card_id=card_id,
            card_name=card.card_name,
            actual_balance=actual_balance,
            expected_balance=expected_balance,
            variance=round(variance, 2),
            status=status,
        )
