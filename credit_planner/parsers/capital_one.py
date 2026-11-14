"""Capital One statement parser implementation."""
import re
from datetime import date
from credit_planner.models import StatementData
from credit_planner.parsers.base import BaseStatementParser


class CapitalOneParser(BaseStatementParser):
    issuer_name = "Capital One"

    def confidence(self, text: str) -> float:
        lower_text = text.lower()
        score = 0.0
        if "capital one" in lower_text or "capitalone" in lower_text:
            score += 0.6
        if "mastercard account no." in lower_text or "capitalone.co.uk" in lower_text:
            score += 0.3
        if "your new balance" in lower_text or "your account summary" in lower_text:
            score += 0.2
        return min(score, 1.0)

    def parse_text(self, text: str) -> StatementData:
        currency = self.detect_currency(text)

        # 1. Statement Balance
        # Matches: "Your new balance £2,234.63" or "NEW CLOSING BALANCE ... £2,234.63"
        balance_match = re.search(
            r"(?:Your\s+new\s+balance|NEW\s+CLOSING\s+BALANCE|New\s+Balance)\s*[:]?\s*\n?\s*([£$€₱]?[\d,]+\.\d{2})",
            text,
            re.IGNORECASE,
        )
        if not balance_match:
            balance_match = re.search(
                r"NEW\s+CLOSING\s+BALANCE[^\n]*\n[^\n]*([£$€₱]?[\d,]+\.\d{2})",
                text,
                re.IGNORECASE,
            )
        balance = self.clean_amount(balance_match.group(1)) if balance_match else 0.0

        # 2. Minimum Payment Due
        # Matches: "This month's minimum payment is £121.91"
        min_match = re.search(
            r"minimum\s+payment\s*(?:is)?\s*[:]?\s*\n?\s*([£$€₱]?[\d,]+\.\d{2})",
            text,
            re.IGNORECASE,
        )
        minimum_payment = self.clean_amount(min_match.group(1)) if min_match else 0.0

        # 3. Payment Due Date
        # Matches: "It's due on 03 Dec 26" or "Payment Due Date: ..."
        due_date_match = re.search(
            r"(?:It's\s+due\s+on|Payment\s+Due\s+Date|Due\s+Date)\s*[:]?\s*\n?\s*([0-9]{1,2}\s+[A-Za-z]+\s+[0-9]{2,4}|\d{1,2}/\d{1,2}/\d{2,4})",
            text,
            re.IGNORECASE,
        )
        due_date = date.today()
        if due_date_match:
            due_date = self.parse_flexible_date(due_date_match.group(1).strip())

        # 4. Statement Date
        # Matches: "Statement date 7 November 26"
        stmt_date_match = re.search(
            r"(?:Statement\s+date|Date)\s*[:]?\s*\n?\s*([0-9]{1,2}\s+[A-Za-z]+\s+[0-9]{2,4}|\d{1,2}/\d{1,2}/\d{2,4})",
            text,
            re.IGNORECASE,
        )
        statement_date = date.today()
        if stmt_date_match:
            statement_date = self.parse_flexible_date(stmt_date_match.group(1).strip())

        # 5. Purchase APR
        # Matches: "Standard Purchase: 30.340%"
        apr_match = re.search(
            r"(?:Standard\s+Purchase|Purchase\s+Rate|Purchase\s+APR)\s*[:]?\s*\n?\s*([\d.]+)%",
            text,
            re.IGNORECASE,
        )
        purchase_apr = float(apr_match.group(1)) if apr_match else 0.0

        # 6. Account Last 4 Digits
        # Matches: "MasterCard Account No. **** **** **** 6067" or "**** **** **** 6067"
        last4_match = re.search(
            r"(?:Account\s*No\.?|Account\s*Number)\s*[:]?\s*\n?\s*(?:\*{4}[\s*]+){3}(\d{4})",
            text,
            re.IGNORECASE,
        )
        if not last4_match:
            last4_match = re.search(r"\*{4}\s+\*{4}\s+\*{4}\s+(\d{4})", text)
        last4 = last4_match.group(1) if last4_match else "0000"

        return StatementData(
            issuer="Capital One",
            statement_date=statement_date,
            statement_balance=balance,
            minimum_payment=minimum_payment,
            due_date=due_date,
            purchase_apr=purchase_apr,
            account_last4=last4,
            currency=currency,
        )
