"""Universal heuristic fallback statement parser for any credit card issuer."""
import re
from datetime import date
from credit_planner.models import StatementData
from credit_planner.parsers.base import BaseStatementParser


class GenericFallbackParser(BaseStatementParser):
    issuer_name = "Generic"

    def confidence(self, text: str) -> float:
        # Fallback parser handles any statement with at least a recognizable balance pattern
        if re.search(r"(?:Balance|Payment|APR)", text, re.IGNORECASE):
            return 0.50
        return 0.10

    def parse_text(self, text: str) -> StatementData:
        currency = self.detect_currency(text)

        # 1. Balance pattern
        balance_match = re.search(
            r"(?:Current\s+Balance\s+Due|New\s+Balance|Statement\s+Balance|Total\s+Balance\s+Due|Amount\s+Due)\s*[:]?\s*([£$€₱]?[\d,]+\.\d{2})",
            text,
            re.IGNORECASE,
        )
        balance = self.clean_amount(balance_match.group(1)) if balance_match else 0.0

        # 2. Minimum Payment
        min_match = re.search(
            r"Minimum\s+Payment(?:\s+Due)?\s*[:]?\s*([£$€₱]?[\d,]+\.\d{2})",
            text,
            re.IGNORECASE,
        )
        minimum_payment = self.clean_amount(min_match.group(1)) if min_match else 0.0

        # 3. Payment Due Date
        due_match = re.search(
            r"Payment\s+Due\s+Date\s*[:]?\s*([\w\s,/-]+?)(?:\n|Card|$)",
            text,
            re.IGNORECASE,
        )
        due_date = self.parse_flexible_date(due_match.group(1)) if due_match else date.today()

        # 4. Statement Date
        stmt_match = re.search(
            r"(?:Statement\s+(?:Closing\s+)?Date|Billing\s+Date)\s*[:]?\s*([\w\s,/-]+?)(?:\n|Payment|$)",
            text,
            re.IGNORECASE,
        )
        statement_date = self.parse_flexible_date(stmt_match.group(1)) if stmt_match else date.today()

        # 5. Purchase APR
        apr_match = re.search(
            r"(?:Annual\s+Percentage\s+Rate|Purchase\s+APR|Purchases\s+APR|APR)\s*[:]?\s*([\d.]+)%",
            text,
            re.IGNORECASE,
        )
        purchase_apr = float(apr_match.group(1)) if apr_match else 0.0

        # 6. Account last 4
        last4_match = re.search(r"(?:Card\s+ending\s+in|Account\s*(?:Number)?)\s*[:]?\s*(?:\*+\s*)*(\d{4})", text, re.IGNORECASE)
        last4 = last4_match.group(1) if last4_match else "0000"

        return StatementData(
            issuer="Generic",
            statement_date=statement_date,
            statement_balance=balance,
            minimum_payment=minimum_payment,
            due_date=due_date,
            purchase_apr=purchase_apr,
            account_last4=last4,
            currency=currency,
        )
