import pytest
from datetime import date
from credit_planner.parsers.detector import IssuerDetector
from credit_planner.parsers.hsbc import HSBCParser
from credit_planner.parsers.generic import GenericFallbackParser
from credit_planner.parsers.registry import ParserRegistry
from tests.fixtures.mock_statements import (
    SAMPLE_HSBC_UK_TEXT,
    SAMPLE_HSBC_US_TEXT,
    SAMPLE_CHASE_GENERIC_TEXT,
    SAMPLE_GENERIC_CARD_TEXT,
    SAMPLE_UNRECOGNIZED_NO_BALANCE,
)

def test_issuer_detector_confidence():
    detector = IssuerDetector()
    
    # HSBC UK Text
    detected, conf = detector.detect(SAMPLE_HSBC_UK_TEXT)
    assert detected == "HSBC"
    assert conf >= 0.8

    # Chase Text
    detected_chase, conf_chase = detector.detect(SAMPLE_CHASE_GENERIC_TEXT)
    assert detected_chase == "Chase"
    assert conf_chase >= 0.8

    # Generic Card Text
    detected_gen, conf_gen = detector.detect(SAMPLE_GENERIC_CARD_TEXT)
    assert detected_gen == "Generic"

def test_hsbc_parser_uk():
    parser = HSBCParser()
    assert parser.confidence(SAMPLE_HSBC_UK_TEXT) >= 0.8

    stmt = parser.parse_text(SAMPLE_HSBC_UK_TEXT)
    assert stmt.issuer == "HSBC"
    assert stmt.statement_balance == 4500.50
    assert stmt.minimum_payment == 120.00
    assert stmt.purchase_apr == 24.99
    assert stmt.account_last4 == "4321"
    assert stmt.currency == "GBP"

def test_hsbc_parser_us():
    parser = HSBCParser()
    stmt = parser.parse_text(SAMPLE_HSBC_US_TEXT)
    assert stmt.issuer == "HSBC"
    assert stmt.statement_balance == 3250.75
    assert stmt.minimum_payment == 95.00
    assert stmt.purchase_apr == 22.49
    assert stmt.account_last4 == "8812"
    assert stmt.currency == "USD"

def test_generic_fallback_parser():
    parser = GenericFallbackParser()
    stmt = parser.parse_text(SAMPLE_GENERIC_CARD_TEXT)
    assert stmt.statement_balance == 1800.25
    assert stmt.minimum_payment == 50.00
    assert stmt.purchase_apr == 19.99
    assert stmt.account_last4 == "5544"

def test_parser_registry_auto_resolve():
    registry = ParserRegistry()
    
    # Resolves HSBC
    parser = registry.resolve_for_text(SAMPLE_HSBC_UK_TEXT)
    assert isinstance(parser, HSBCParser)

    # Resolves Generic for unrecognized banks
    gen_parser = registry.resolve_for_text(SAMPLE_GENERIC_CARD_TEXT)
    assert isinstance(gen_parser, GenericFallbackParser)
