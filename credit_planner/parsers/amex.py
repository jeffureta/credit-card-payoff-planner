"""American Express statement parser implementation."""
import re
from datetime import date
from credit_planner.models import StatementData
from credit_planner.parsers.base import BaseStatementParser


class AmexParser(BaseStatementParser):
    issuer_name = "American Express"

    def confidence(self, text: str) -> float:
        lower_text = text.lower()
        score = 0.0
        if "american express" in lower_text or "americanexpress" in lower_text:
            score += 0.6
        if "membership number" in lower_text or "amex" in lower_text:
            score += 0.3
        if "closing balance" in lower_text or "minimum repayment" in lower_text:
            score += 0.2
        return min(score, 1.0)

    def parse_text(self, text: str) -> StatementData:
        currency = self.detect_currency(text)
        # Normalize whitespace while preserving essential structure
        norm_text = re.sub(r"[ \t]+", " ", text)
        collapsed_text = re.sub(r"\s+", " ", text)

        # 1. Statement Balance
        # On Amex statement tables, "Closing Balance\nAccount Summary\n1,385.24" appears
        balance_match = re.search(
            r"Closing\s+Balance[^\d\n]*\n?(?:Account\s+Summary\s*\n?)?([£$€₱]?[\d,]+\.\d{2})",
            norm_text,
            re.IGNORECASE,
        )
        if not balance_match:
            balance_match = re.search(
                r"Closing\s+Balance\s+Account\s+Summary\s+([£$€₱]?[\d,]+\.\d{2})",
                collapsed_text,
                re.IGNORECASE,
            )
        if not balance_match:
            balance_match = re.search(
                r"(?:New\s+Balance|Statement\s+Balance)\s*[:]?\s*([£$€₱]?[\d,]+\.\d{2})",
                collapsed_text,
                re.IGNORECASE,
            )
        balance = self.clean_amount(balance_match.group(1)) if balance_match else 0.0

        # 2. Minimum Payment Due
        # Matches: "Please send your minimum repayment of £ 59.42 by the due date"
        # Or table summary: "Minimum Repayment ... 59.42"
        min_match = re.search(
            r"minimum\s+repayment\s+of\s*[£$€₱]?\s*([\d,]+\.\d{2})",
            collapsed_text,
            re.IGNORECASE,
        )
        if not min_match:
            min_match = re.search(
                r"Minimum\s+(?:Repayment|Payment)\s*[:]?\s*[£$€₱]?\s*([\d,]+\.\d{2})",
                collapsed_text,
                re.IGNORECASE,
            )
        minimum_payment = self.clean_amount(min_match.group(1)) if min_match else 0.0

        # 3. Payment Due Date
        # Matches: "£ 13 November 2026 1 of 5" or "Payment Due Date ... 13 November 2026"
        due_date_match = re.search(
            r"(?:Payment\s+Due\s+Date|due\s+date\s+shown)[^\n\d]*([0-9]{1,2}\s+[A-Za-z]+\s+[0-9]{2,4})",
            collapsed_text,
            re.IGNORECASE,
        )
        if not due_date_match:
            due_date_match = re.search(
                r"£\s*([0-9]{1,2}\s+[A-Za-z]+\s+[0-9]{2,4})\s+\d+\s+of\s+\d+",
                collapsed_text,
                re.IGNORECASE,
            )
        due_date = date.today()
        if due_date_match:
            due_date = self.parse_flexible_date(due_date_match.group(1).strip())

        # 4. Statement Date
        # Matches: "Date 19/10/26" or "received by 19 October 2026" or "From ... to 19 October 2026"
        stmt_date_match = re.search(
            r"received\s+by\s+([0-9]{1,2}\s+[A-Za-z]+\s+[0-9]{2,4})",
            collapsed_text,
            re.IGNORECASE,
        )
        if not stmt_date_match:
            stmt_date_match = re.search(
                r"to\s+([0-9]{1,2}\s+[A-Za-z]+\s+[0-9]{2,4})\s+At",
                collapsed_text,
                re.IGNORECASE,
            )
        if not stmt_date_match:
            stmt_date_match = re.search(
                r"Date\s*[:]?\s*(\d{1,2}/\d{1,2}/\d{2,4})",
                collapsed_text,
                re.IGNORECASE,
            )
        statement_date = date.today()
        if stmt_date_match:
            statement_date = self.parse_flexible_date(stmt_date_match.group(1).strip())

        # 5. Purchase APR
        # Matches: "Goods And Services 33.2 %" or "Goods and Services 33.2%"
        apr_match = re.search(
            r"Goods\s+And\s+Services\s+([\d.]+)\s*%",
            collapsed_text,
            re.IGNORECASE,
        )
        if not apr_match:
            apr_match = re.search(
                r"(?:Compound\s+Annual\s+Rate|Simple\s+Rate)[^\d%]*([\d.]+)\s*%",
                collapsed_text,
                re.IGNORECASE,
            )
        purchase_apr = float(apr_match.group(1)) if apr_match else 0.0

        # 6. Account Number / Membership Number
        # Matches: "xxxx-xxxxxx-11009" or "xxxx-xxxxxx- 11009"
        last4_match = re.search(
            r"xxxx-xxxxxx-?\s*(\d{4,5})",
            collapsed_text,
            re.IGNORECASE,
        )
        last4 = last4_match.group(1) if last4_match else "0000"

        return StatementData(
            issuer="American Express",
            statement_date=statement_date,
            statement_balance=balance,
            minimum_payment=minimum_payment,
            due_date=due_date,
            purchase_apr=purchase_apr,
            account_last4=last4,
            currency=currency,
        )
