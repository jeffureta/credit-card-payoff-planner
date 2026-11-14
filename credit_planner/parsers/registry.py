"""Parser registry for discovering and executing matching statement parsers."""
from typing import List
from credit_planner.parsers.base import BaseStatementParser
from credit_planner.parsers.hsbc import HSBCParser
from credit_planner.parsers.generic import GenericFallbackParser


class ParserRegistry:
    def __init__(self):
        self.parsers: List[BaseStatementParser] = [
            HSBCParser(),
            # Future parsers (Chase, Amex, etc.) can be registered here
            GenericFallbackParser(),
        ]

    def register(self, parser: BaseStatementParser) -> None:
        # Insert before generic fallback
        self.parsers.insert(0, parser)

    def resolve_for_text(self, text: str) -> BaseStatementParser:
        best_parser = self.parsers[-1]  # Generic default
        max_conf = 0.0

        for parser in self.parsers:
            conf = parser.confidence(text)
            if conf > max_conf:
                max_conf = conf
                best_parser = parser
            if conf >= 0.8:
                return parser

        return best_parser
