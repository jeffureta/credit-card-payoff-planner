"""Vanquis Bank Credit Card Statement Parser (UK)."""
import re
from datetime import date
from credit_planner.models import StatementData
from credit_planner.parsers.base import BaseStatementParser


class VanquisParser(BaseStatementParser):
    issuer_name = "Vanquis"

    def confidence(self, text: str) -> float:
        lower = text.lower()
        if "vanquis" in lower:
            return 0.95
        return 0.0

    def parse_text(self, text: str) -> StatementData:
        currency = self.detect_currency(text)

        # 1. Statement Balance
        # Matches: "This month's balance £4,436.78", "STATEMENT BALANCE = £4,436.78", "New Balance £4,436.78"
        balance_match = re.search(
            r"(?:This\s+month's\s+balance|STATEMENT\s+BALANCE\s*=|New\s+Balance|Statement\s+Balance)\s*[:=]?\s*([£$€₱]?[\d,]+\.\d{2})",
            text,
            re.IGNORECASE,
        )
        balance = self.clean_amount(balance_match.group(1)) if balance_match else 0.0

        # 2. Minimum Payment Due
        # Matches: "This month's minimum payment £150.44", "Minimum payment £150.44"
        min_match = re.search(
            r"(?:This\s+month's\s+minimum\s+payment|Minimum\s+Payment(?:\s+Due)?)\s*[:]?\s*([£$€₱]?[\d,]+\.\d{2})",
            text,
            re.IGNORECASE,
        )
        minimum_payment = self.clean_amount(min_match.group(1)) if min_match else 0.0

        # 3. Payment Due Date
        # Matches: "This must reach your account by 16/11/26", "reach your account by 16/11/2026", "Payment Due Date: 16/11/26"
        due_match = re.search(
            r"(?:reach\s+your\s+account\s+by|Payment\s+Due\s+Date)\s*[:]?\s*([\w\s,/-]+?)(?:\n|$)",
            text,
            re.IGNORECASE,
        )
        due_date = self.parse_flexible_date(due_match.group(1)) if due_match else date.today()

        # 4. Statement Date
        # Matches: "Statement Date: 20 October 2026", "20 October 2026" near statement header
        stmt_date_match = re.search(
            r"(?:Statement\s+Date\s*[:]?\s*([\w\s,/-]+?)(?:\n|$))|(\b\d{1,2}\s+(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{4}\b)",
            text,
            re.IGNORECASE,
        )
        statement_date = date.today()
        if stmt_date_match:
            raw_date = stmt_date_match.group(1) or stmt_date_match.group(2)
            if raw_date:
                statement_date = self.parse_flexible_date(raw_date.strip())

        # 5. Purchase APR
        # Matches monthly purchase interest: "PURCHASE INTEREST 2.30%" -> annualize (2.30 * 12 = 27.60)
        # Or standard APR: "Purchase Rate (APR): 27.6%"
        monthly_match = re.search(
            r"PURCHASE\s+INTEREST\s*[:]?\s*([\d.]+)%",
            text,
            re.IGNORECASE,
        )
        annual_match = re.search(
            r"(?:Purchase\s+Rate\s*\(APR\)|Annual\s+Percentage\s+Rate|Purchase\s+APR)\s*[:]?\s*([\d.]+)%",
            text,
            re.IGNORECASE,
        )
        if monthly_match:
            monthly_rate = float(monthly_match.group(1))
            purchase_apr = round(monthly_rate * 12, 2)
        elif annual_match:
            purchase_apr = float(annual_match.group(1))
        else:
            purchase_apr = 0.0

        # 6. Account Last 4 Digits
        # Matches: "Account Number: 4023 9639 1337 8950" or "**** **** **** 8950"
        last4_match = re.search(
            r"(?:Account\s*(?:Number)?)\s*[:]?\s*(?:\d{4}[\s*]+){3}(\d{4})",
            text,
            re.IGNORECASE,
        )
        if not last4_match:
            # Fallback search for any 16-digit spaced pattern
            card_seq = re.search(r"\b\d{4}\s+[\d*]{4}\s+[\d*]{4}\s+(\d{4})\b", text)
            last4 = card_seq.group(1) if card_seq else "0000"
        else:
            last4 = last4_match.group(1)

        return StatementData(
            issuer="Vanquis",
            statement_date=statement_date,
            statement_balance=balance,
            minimum_payment=minimum_payment,
            due_date=due_date,
            purchase_apr=purchase_apr,
            account_last4=last4,
            currency=currency,
        )
