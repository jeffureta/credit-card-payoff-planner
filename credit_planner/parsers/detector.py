"""Automatic Issuer Detector with confidence scoring."""
import re
from typing import Tuple, Dict, List


class IssuerDetector:
    # Common signature keywords, domains, and phone numbers for major issuers
    SIGNATURES: Dict[str, List[str]] = {
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
        "American Express": [
            r"american\s*express",
            r"\bamex\b",
            r"americanexpress\.com",
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
        "Capital One": [
            r"capital\s*one",
            r"capitalone\.com",
            r"quicksilver",
            r"venture\s*x",
        ],
        "Vanquis": [
            r"\bvanquis\b",
            r"vanquis\s*bank",
            r"vanquis\s*card",
            r"vanquis\.co\.uk",
            r"vanquis\.com",
        ],
    }

    def detect(self, text: str) -> Tuple[str, float]:
        """Detects the credit card company from text and returns (issuer_name, confidence)."""
        lower_text = text.lower()
        best_issuer = "Generic"
        max_matches = 0

        for issuer, patterns in self.SIGNATURES.items():
            matches = sum(1 for p in patterns if re.search(p, lower_text))
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
