"""Base statement parser abstract interface and normalization utilities."""
import re
from abc import ABC, abstractmethod
from datetime import date, datetime
from typing import Optional, Tuple
from credit_planner.models import StatementData


class BaseStatementParser(ABC):
    issuer_name: str = "Generic"

    @abstractmethod
    def confidence(self, text: str) -> float:
        """Returns a score between 0.0 and 1.0 indicating parser confidence."""
        pass

    @abstractmethod
    def parse_text(self, text: str) -> StatementData:
        """Parses extracted statement text into a normalized StatementData model."""
        pass

    @staticmethod
    def clean_amount(val_str: str) -> float:
        """Extracts float amount from currency strings (e.g. '$1,234.56' -> 1234.56)."""
        cleaned = re.sub(r"[^\d.]", "", val_str)
        return float(cleaned) if cleaned else 0.0

    @staticmethod
    def clean_percentage(val_str: str) -> float:
        """Extracts float percentage from rate strings (e.g. '24.99%' -> 24.99)."""
        cleaned = re.sub(r"[^\d.]", "", val_str)
        return float(cleaned) if cleaned else 0.0

    @staticmethod
    def parse_flexible_date(date_str: str) -> date:
        """Parses dates from common statement formats (e.g. 15 October 2026, 11/10/2026, 2026-10-15)."""
        date_str = date_str.strip()
        formats = [
            "%d %B %Y",
            "%d %b %Y",
            "%d %B %y",
            "%d %b %y",
            "%B %d, %Y",
            "%b %d, %Y",
            "%B %d, %y",
            "%b %d, %y",
            "%B %d %Y",
            "%b %d %Y",
            "%B %d %y",
            "%b %d %y",
            "%m/%d/%Y",
            "%d/%m/%Y",
            "%d/%m/%y",
            "%m/%d/%y",
            "%Y-%m-%d",
        ]
        for fmt in formats:
            try:
                return datetime.strptime(date_str, fmt).date()
            except ValueError:
                continue
        # Default fallback to today's date if date cannot be parsed
        return date.today()

    @staticmethod
    def detect_currency(text: str) -> str:
        if "£" in text or "GBP" in text:
            return "GBP"
        if "€" in text or "EUR" in text:
            return "EUR"
        if "₱" in text or "PHP" in text:
            return "PHP"
        if "HK$" in text or "HKD" in text:
            return "HKD"
        return "USD"
