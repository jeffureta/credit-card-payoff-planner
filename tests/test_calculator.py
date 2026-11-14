import pytest
from credit_planner.calculator import (
    calculate_monthly_interest,
    amortize_card,
    solve_payment_for_target_months,
    AmortizationRow,
    PayoffPlanResult,
)

def test_monthly_interest_calculation():
    # Balance: $10,000, APR: 24.0% -> Monthly rate = 2.0% -> Interest = $200.00
    interest = calculate_monthly_interest(balance=10000.0, annual_apr=24.0)
    assert round(interest, 2) == 200.00

def test_amortization_fixed_payment():
    # Balance: $1,000, APR: 12.0% (1% monthly), Monthly Payment: $300
    # Month 1: Interest = 10.0, Principal = 290.0, Ending = 710.0
    # Month 2: Interest = 7.10, Principal = 292.90, Ending = 417.10
    # Month 3: Interest = 4.17, Principal = 295.83, Ending = 121.27
    # Month 4: Interest = 1.21, Final Payment = 122.48, Ending = 0.0
    result = amortize_card(balance=1000.0, annual_apr=12.0, monthly_payment=300.0)
    assert isinstance(result, PayoffPlanResult)
    assert result.months == 4
    assert round(result.total_interest, 2) == pytest.approx(22.48, abs=0.1)
    assert result.schedule[-1].ending_balance == 0.0

def test_negative_amortization_error():
    # Balance: $5,000, APR: 24.0% -> Monthly Interest = $100.
    # Monthly payment of $80 is less than interest -> Debt will grow infinitely!
    with pytest.raises(ValueError, match="Monthly payment.*cannot cover monthly interest"):
        amortize_card(balance=5000.0, annual_apr=24.0, monthly_payment=80.0)

def test_solve_payment_for_target_months():
    # Balance: $2,400, APR: 18.0%, Target: 12 months
    monthly_payment = solve_payment_for_target_months(balance=2400.0, annual_apr=18.0, target_months=12)
    assert monthly_payment > 200.0  # Must be higher than 2400/12 due to interest
    
    # Verify amortization with solved payment completes in exactly 12 months
    result = amortize_card(balance=2400.0, annual_apr=18.0, monthly_payment=monthly_payment)
    assert result.months == 12
    assert result.schedule[-1].ending_balance == 0.0
