"""HSBC Credit Card Statement Parser (UK, US, HK, PH variations)."""
import re
from datetime import date
from credit_planner.models import StatementData
from credit_planner.parsers.base import BaseStatementParser


class HSBCParser(BaseStatementParser):
    issuer_name = "HSBC"

    def confidence(self, text: str) -> float:
        lower = text.lower()
        if "hsbc" in lower:
            return 0.95
        return 0.0

    def parse_text(self, text: str) -> StatementData:
        currency = self.detect_currency(text)

        # 1. Statement Balance
        # Matches: "New Statement Balance: £4,500.50", "New Balance: $3,250.75"
        balance_match = re.search(
            r"(?:New\s+Statement\s+Balance|New\s+Balance|Statement\s+Balance|Total\s+Balance)\s*[:]?\s*([£$€₱]?[\d,]+\.\d{2})",
            text,
            re.IGNORECASE,
        )
        balance = self.clean_amount(balance_match.group(1)) if balance_match else 0.0

        # 2. Minimum Payment Due
        min_match = re.search(
            r"Minimum\s+Payment\s*(?:Due)?\s*[:]?\s*([£$€₱]?[\d,]+\.\d{2})",
            text,
            re.IGNORECASE,
        )
        minimum_payment = self.clean_amount(min_match.group(1)) if min_match else 0.0

        # 3. Payment Due Date
        due_match = re.search(
            r"Payment\s+Due\s+Date\s*[:]?\s*([\w\s,/-]+?)(?:\n|Account|$)",
            text,
            re.IGNORECASE,
        )
        due_date = self.parse_flexible_date(due_match.group(1)) if due_match else date.today()

        # 4. Statement Date
        stmt_date_match = re.search(
            r"(?:Statement\s+Date|Statement\s+Period|Date)\s*[:]?\s*([\w\s,/-]+?)(?:\n|Payment|to|$)",
            text,
            re.IGNORECASE,
        )
        statement_date = (
            self.parse_flexible_date(stmt_date_match.group(1)) if stmt_date_match else date.today()
        )

        # 5. Purchase APR
        apr_match = re.search(
            r"(?:Purchase\s+Rate\s*\(APR\)|Annual\s+Percentage\s+Rate\s*\(APR\)|Purchases:\s*Annual\s+Percentage\s+Rate\s*\(APR\)|Purchase\s+APR)\s*[:]?\s*([\d.]+)%",
            text,
            re.IGNORECASE,
        )
        purchase_apr = float(apr_match.group(1)) if apr_match else 0.0

        # 6. Last 4 Digits
        last4_match = re.search(r"(?:Account\s*(?:Number|Ending\s+In)?)\s*[:]?\s*(?:\*+\s*)*(\d{4})", text, re.IGNORECASE)
        last4 = last4_match.group(1) if last4_match else "0000"

        return StatementData(
            issuer="HSBC",
            statement_date=statement_date,
            statement_balance=balance,
            minimum_payment=minimum_payment,
            due_date=due_date,
            purchase_apr=purchase_apr,
            account_last4=last4,
            currency=currency,
        )
