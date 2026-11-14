import pytest
from credit_planner.strategies import (
    simulate_multi_card_payoff,
    DebtCardInput,
    MultiCardStrategyComparison,
)

def test_avalanche_vs_snowball_simulation():
    # Card 1: $1,000 balance, 26.0% APR, $30 min payment
    # Card 2: $3,000 balance, 15.0% APR, $75 min payment
    cards = [
        DebtCardInput(id=1, name="High APR Card", balance=1000.0, apr=26.0, min_payment=30.0),
        DebtCardInput(id=2, name="Lower APR Card", balance=3000.0, apr=15.0, min_payment=75.0),
    ]
    # Total minimum payments = $105
    # Total monthly budget = $300 (extra $195 rollover)
    comparison = simulate_multi_card_payoff(cards=cards, total_monthly_budget=300.0)

    assert isinstance(comparison, MultiCardStrategyComparison)
    # Avalanche mathematically saves equal or more interest than Snowball
    assert comparison.avalanche_result.total_interest <= comparison.snowball_result.total_interest
    assert comparison.avalanche_result.months > 0
    assert comparison.snowball_result.months > 0
    # Both strategies must fully eliminate the total debt
    assert comparison.avalanche_result.total_remaining_debt == 0.0
    assert comparison.snowball_result.total_remaining_debt == 0.0

def test_insufficient_multi_card_budget():
    cards = [
        DebtCardInput(id=1, name="Card 1", balance=2000.0, apr=20.0, min_payment=50.0),
        DebtCardInput(id=2, name="Card 2", balance=4000.0, apr=24.0, min_payment=100.0),
    ]
    # Total min payment is $150. Budget of $120 cannot even cover minimums!
    with pytest.raises(ValueError, match="Total monthly budget.*less than minimum required payments"):
        simulate_multi_card_payoff(cards=cards, total_monthly_budget=120.0)
