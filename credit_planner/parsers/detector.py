"""Automatic Issuer Detector with confidence scoring."""
import re
from typing import Tuple, Dict, List


class IssuerDetector:
    # Common signature keywords, domains, and phone numbers for major issuers
    SIGNATURES: Dict[str, List[str]] = {
        "Capital One": [
            r"capital\s*one",
            r"capitalone\.co(?:m|\.uk)",
            r"quicksilver",
            r"venture\s*x",
            r"mastercard\s*account\s*no\.",
        ],
        "American Express": [
            r"american\s*express",
            r"\bamex\b",
            r"americanexpress\.co(?:m|\.uk)",
            r"membership\s*number",
        ],
        "Vanquis": [
            r"\bvanquis\b",
            r"vanquis\s*bank",
            r"vanquis\s*card",
            r"vanquis\.co\.uk",
            r"vanquis\.com",
        ],
        "HSBC": [
            r"\bhsbc\b",
            r"hsbc\s*bank",
            r"hsbc\s*uk",
            r"hsbcusa\.com",
            r"hsbc\.co\.uk",
            r"hsbc\.com\.ph",
            r"hsbc\.com\.hk",
        ],
        "Chase": [
            r"\bchase\b",
            r"jpmorgan\s*chase",
            r"chase\.com",
            r"sapphire\s*preferred",
            r"sapphire\s*reserve",
            r"freedom\s*unlimited",
        ],
        "Citibank": [
            r"\bcitibank\b",
            r"\bciti\b",
            r"citi\.com",
            r"citi\s*double\s*cash",
        ],
        "Discover": [
            r"\bdiscover\b",
            r"discover\s*bank",
            r"discover\.com",
            r"discover\s*it",
        ],
    }

    def detect(self, text: str) -> Tuple[str, float]:
        """Detects the credit card company from text and returns (issuer_name, confidence)."""
        lower_text = text.lower()

        # Pre-filter out third-party collection / payment slip references that cause false positives
        # E.g. Capital One statements have a tear-off payment slip saying:
        # "HSBC Bank plc Head Office Collection Account Capital One"
        filtered_hsbc_text = re.sub(
            r"hsbc\s*bank\s*plc\s*(?:head\s*office\s*collection\s*account)?",
            "",
            lower_text,
            flags=re.IGNORECASE,
        ) if ("capital one" in lower_text or "vanquis" in lower_text or "american express" in lower_text) else lower_text

        best_issuer = "Generic"
        max_matches = 0

        for issuer, patterns in self.SIGNATURES.items():
            target_text = filtered_hsbc_text if issuer == "HSBC" else lower_text
            matches = sum(1 for p in patterns if re.search(p, target_text))
            if matches > max_matches:
                max_matches = matches
                best_issuer = issuer

        if max_matches >= 2:
            confidence = 0.95
        elif max_matches == 1:
            confidence = 0.85
        else:
            best_issuer = "Generic"
            confidence = 0.50

        return best_issuer, confidence
